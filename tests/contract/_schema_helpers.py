"""Small, dependency-free helpers shared by the `tests/contract/` CT-00
suite. A plain top-level module (not part of the `tests`/`tests.contract`
package hierarchy, which has no `__init__.py` by design - see
`docs/handover/PACK-01-REPORT.md` on `--import-mode=importlib`) - imported
as `from _schema_helpers import ...` after `conftest.py` puts this
directory on `sys.path`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS_DIR = REPO_ROOT / "contracts" / "schemas"
EVENTS_DIR = REPO_ROOT / "contracts" / "events"
REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-02.yml"
OPENAPI_PATH = REPO_ROOT / "contracts" / "openapi" / "pack-02.yaml"
SERVICES_DIR = REPO_ROOT / "services"

#: PACK-03's own reason-code registry / OpenAPI contract - added alongside
#: (never replacing) the PACK-02 constants above, so existing PACK-02
#: call sites are completely unaffected.
PACK03_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-03.yml"
PACK03_OPENAPI_PATH = REPO_ROOT / "contracts" / "openapi" / "pack-03.yaml"

#: Exactly which service directories belong to which pack - used so a
#: registry/contract scan can be scoped to its own pack's services rather
#: than indiscriminately scanning the whole `services/` tree (which now
#: contains both packs' services) against a single pack's registry. See
#: `test_reason_codes_registry.py`.
PACK02_SERVICE_DIRS: tuple[str, ...] = (
    "account-service",
    "identity-service",
    "eligibility-service",
    "credential-service",
    "audit-core",
)
PACK03_SERVICE_DIRS: tuple[str, ...] = (
    "initiative-service",
    "deliberation-service",
    "moderation-service",
    "voting-service",
    "tally-service",
    "delegation-service",
)


def load_schema(name: str) -> dict[str, Any]:
    parsed: dict[str, Any] = json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))
    return parsed


def load_event_schema(name: str) -> dict[str, Any]:
    parsed: dict[str, Any] = json.loads((EVENTS_DIR / name).read_text(encoding="utf-8"))
    return parsed


def to_jsonable(value: Mapping[str, Any]) -> dict[str, Any]:
    """Round-trip a payload dict through `json` so UUID/datetime/Enum
    values become plain JSON types, the same shape a real wire payload
    would have."""
    parsed: dict[str, Any] = json.loads(json.dumps(value, default=str))
    return parsed


def envelope_to_jsonable(envelope: Any) -> dict[str, Any]:
    return {
        "event_id": str(envelope.event_id),
        "event_type": envelope.event_type,
        "event_version": envelope.event_version,
        "occurred_at": envelope.occurred_at.isoformat(),
        "producer": envelope.producer,
        "actor": {
            "actor_id": str(envelope.actor.actor_id),
            "actor_type": envelope.actor.actor_type,
        },
        "subject": {
            "subject_type": envelope.subject.subject_type,
            "subject_id": str(envelope.subject.subject_id),
        },
        "correlation_id": str(envelope.correlation_id),
        "causation_id": str(envelope.causation_id) if envelope.causation_id else None,
        "payload": to_jsonable(envelope.payload),
        "integrity": {
            "payload_hash": envelope.integrity.payload_hash,
            "signature": envelope.integrity.signature,
        },
    }
