"""Deployment/release identity foundation (INFRA01-HI-09, FIR-REL-001).

Machine-readable validation of an integrated deployment manifest. The
invariant enforced here is::

    running combination == one approved deployment manifest

and explicitly **not** ``all services must be identical version``. A manifest
whose components carry heterogeneous source revisions is valid only when its
compatibility matrix explicitly declares evidence for the exact combination;
absence of compatibility evidence means the combination is not deployable
(:data:`codes.COMPATIBILITY_NOT_DECLARED`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from scripts.acceptance import codes
from scripts.acceptance.canonical import load_json, verify_sealed_document

SCHEMA_FILE = Path(__file__).resolve().parent / "schemas/deployment_manifest.schema.json"


@dataclass(frozen=True)
class ManifestFinding:
    code: str
    detail: str


def load_schema(schema_file: Path = SCHEMA_FILE) -> dict[str, Any]:
    schema = load_json(schema_file)
    if not isinstance(schema, dict):
        raise ValueError(f"deployment-manifest schema is not an object: {schema_file}")
    return schema


def validate_manifest(document: dict[str, Any]) -> list[ManifestFinding]:
    """Fail-closed validation of one deployment manifest document."""
    findings: list[ManifestFinding] = []
    validator = jsonschema.Draft202012Validator(load_schema())
    for error in sorted(validator.iter_errors(document), key=lambda item: str(item.json_path)):
        findings.append(
            ManifestFinding(
                codes.DEPLOYMENT_MANIFEST_INVALID, f"{error.json_path}: {error.message}"
            )
        )
    if findings:
        return findings

    components = document["components"]
    revisions = {str(component["source_revision"]) for component in components}
    compatibility = document["compatibility"]
    mode = str(compatibility["mode"])

    if len(revisions) > 1:
        if mode != "mixed-by-declared-matrix":
            findings.append(
                ManifestFinding(
                    codes.COMPATIBILITY_NOT_DECLARED,
                    "components carry heterogeneous source revisions but compatibility mode "
                    "is not 'mixed-by-declared-matrix'",
                )
            )
        else:
            matrix = compatibility.get("matrix") or []
            actual = {str(c["name"]): str(c["source_revision"]) for c in components}
            covered = any(
                all(actual.get(name) == revision for name, revision in entry["components"].items())
                and set(entry["components"]) == set(actual)
                for entry in matrix
            )
            if not covered:
                findings.append(
                    ManifestFinding(
                        codes.COMPATIBILITY_NOT_DECLARED,
                        "no compatibility-matrix entry covers the exact running combination; "
                        "the combination is not deployable",
                    )
                )
    if "manifest_sha256" in document and not verify_sealed_document(document):
        findings.append(
            ManifestFinding(
                codes.MANIFEST_INTEGRITY_FAILURE,
                "deployment manifest integrity digest does not match its content",
            )
        )
    return findings
