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

#: PACK-04's own reason-code registry / OpenAPI contract - added alongside
#: (never replacing) the PACK-02/PACK-03 constants above.
PACK04_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-04.yml"
PACK04_OPENAPI_PATH = REPO_ROOT / "contracts" / "openapi" / "pack-04.yaml"

#: PACK-05's own reason-code registry / OpenAPI contract - added alongside
#: (never replacing) the PACK-02/PACK-03/PACK-04 constants above.
PACK05_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-05.yml"
PACK05_OPENAPI_PATH = REPO_ROOT / "contracts" / "openapi" / "pack-05.yaml"

#: PACK-06's own reason-code registry / OpenAPI contract - added alongside
#: (never replacing) the PACK-02/PACK-03/PACK-04/PACK-05 constants above.
PACK06_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-06.yml"
PACK06_OPENAPI_PATH = REPO_ROOT / "contracts" / "openapi" / "pack-06.yaml"

#: PACK-07's own reason-code registry / OpenAPI contract (canon-0.6.0
#: implementation round, ADR-026 through ADR-031) - added alongside
#: (never replacing) the PACK-02 through PACK-06 constants above.
PACK07_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-07.yml"
PACK07_OPENAPI_PATH = REPO_ROOT / "contracts" / "openapi" / "pack-07.yaml"

#: PACK-08's own reason-code registry / OpenAPI contract (canon-0.7.0
#: implementation round, section 19e, ADR-032 through ADR-037) - added
#: alongside (never replacing) the PACK-02 through PACK-07 constants
#: above.
PACK08_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-08.yml"
PACK08_OPENAPI_PATH = REPO_ROOT / "contracts" / "openapi" / "pack-08.yaml"

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
PACK04_SERVICE_DIRS: tuple[str, ...] = ("transparency-service",)
PACK05_SERVICE_DIRS: tuple[str, ...] = ("governance-service",)
PACK06_SERVICE_DIRS: tuple[str, ...] = ("ai-processing-service",)
#: PACK-07's one wholly new service (membership-service). Unlike every
#: pack above, PACK-07 does NOT introduce a disjoint set of service
#: directories for all of its functionality - it also extends two
#: existing PACK-02 services (identity-service, eligibility-service) in
#: place. Those two are intentionally NOT listed here; they stay in
#: PACK02_SERVICE_DIRS and are handled by
#: `PACK07_SHARED_WITH_PACK02_SERVICE_DIRS` below instead, since their
#: `src/` trees mix genuinely-PACK-02 and genuinely-PACK-07 reason-code
#: literals together.
PACK07_SERVICE_DIRS: tuple[str, ...] = ("membership-service",)
#: PACK-08's one wholly new service (organization-service). Like PACK-02
#: through PACK-06 (and unlike PACK-07), PACK-08 introduces a fully
#: disjoint service directory - no existing service is extended in place
#: this round, so no "shared with an earlier pack" union is needed here.
PACK08_SERVICE_DIRS: tuple[str, ...] = ("organization-service",)

#: identity-service and eligibility-service (both already listed in
#: `PACK02_SERVICE_DIRS` above) also gained PACK-07 additive reason-code
#: literals in this implementation round (ADR-026 through ADR-031).
#: `test_reason_codes_registry.py` handles this by unioning pack-02.yml
#: with pack-07.yml for pack-02's own literal-usage scan (see that file's
#: `_EXTRA_REGISTRIES_FOR_LITERAL_CHECK`) rather than splitting
#: `PACK02_SERVICE_DIRS` itself - simpler, and safe here since neither
#: account-service nor credential-service (the other two PACK02_SERVICE_DIRS
#: entries) uses any PACK-07 code.


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
