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

#: PACK-09's own reason-code registry / OpenAPI contract (Compliance,
#: Records Governance & Legal Workflows; ADR-038 through ADR-042) - added
#: alongside (never replacing) the PACK-02 through PACK-08 constants
#: above. Canon stays at 0.7.0 this round: PACK-09 introduced no canon
#: amendment, so there is no new canon-owned constant here.
PACK09_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-09.yml"
PACK09_OPENAPI_PATH = REPO_ROOT / "contracts" / "openapi" / "pack-09.yaml"

#: PACK-10's own reason-code registry (Party Finance, Accounting &
#: Rechenschaftsbericht; canon 0.8.0 section 19f, ADR-048 through
#: ADR-054) - added alongside (never replacing) the PACK-02 through
#: PACK-09 constants above. There is deliberately no
#: `PACK10_OPENAPI_PATH`: this round exposes no HTTP surface, so no
#: OpenAPI contract exists to point at, and inventing one would make the
#: contract suite assert against a file that describes nothing runnable.
PACK10_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-10.yml"

#: PACK-11's own reason-code registry (Governed Documents & Evidence;
#: FIR-ROADMAP-001, FIR-INV-010, ADR-055 through ADR-060) - added
#: alongside (never replacing) the PACK-02 through PACK-10 constants
#: above. There is deliberately no `PACK11_OPENAPI_PATH`, for the same
#: reason PACK-10 has none: this round exposes no HTTP surface, so no
#: OpenAPI contract exists to point at, and inventing one would make the
#: contract suite assert against a file that describes nothing runnable.
#:
#: There is also no PACK-11 canon constant. Canon stays at 0.8.0: this
#: round amends no canon, and every DOCUMENT_* code in the registry is an
#: additive `source: pack-11-service` code (ADR-055) rather than a
#: canon-owned one, because canon section 24 registers no document or
#: evidence code at all.
PACK11_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-11.yml"

#: PACK-12's own reason-code registry (Privileged Administration,
#: Authorization-Aware Search & Governed Data Export; FIR-ROADMAP-002,
#: ADR-061 through ADR-068) - added alongside (never replacing) the
#: PACK-02 through PACK-11 constants above. There is deliberately no
#: `PACK12_OPENAPI_PATH`, for the same reason PACK-10 and PACK-11 have
#: none: this round exposes no HTTP surface, so no OpenAPI contract exists
#: to point at, and inventing one would make the contract suite assert
#: against a file that describes nothing runnable.
#:
#: There is also no PACK-12 canon constant. Canon stays at 0.8.0: this
#: round amends no canon, and every PRIVILEGE_*, SEARCH_*, EXPORT_* and
#: DISCLOSURE_* code in the registry is an additive `source:
#: pack-12-service` code (ADR-061) rather than a canon-owned one, because
#: canon section 24 registers no privileged-administration, search or
#: export code at all.
PACK12_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-12.yml"

#: PACK-13's own reason-code registry (Production Data Plane & Contract
#: Evolution; ADR-069 through ADR-078) - added alongside (never
#: replacing) the PACK-02 through PACK-12 constants above. There is
#: deliberately no `PACK13_OPENAPI_PATH`, for the same reason PACK-10,
#: PACK-11 and PACK-12 have none: PACK-13 exposes no new public HTTP
#: surface, only contract-level administrative view models.
PACK13_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-13.yml"

#: PACK-14's own reason-code registry (Identity, Authentication & Account
#: Security; FIR-ROADMAP-004, ADR-079 through ADR-088) - added alongside
#: (never replacing) the PACK-02 through PACK-13 constants above. There
#: is deliberately no `PACK14_OPENAPI_PATH`, for the same reason PACK-10
#: through PACK-13 have none: PACK-14 exposes no new public HTTP surface,
#: only the contract-level endpoint catalogue in
#: `epd2_identity_service.api`.
#:
#: There is also no PACK-14 canon constant. Canon stays at 0.8.0: this
#: round amends no canon, reuses canon 19d.2's and 19d.8's existing
#: four-value assurance scale rather than inventing an AAL-0..3
#: vocabulary, and every CREDENTIAL_*, MFA_*, ASSURANCE_*, STEP_UP_*,
#: SESSION_*, ACCOUNT_*, RECOVERY_*, CONTACT_*, BOOTSTRAP_* and
#: VOTING_HANDOFF_* code in the registry is an additive
#: `pack-14-service` code justified in ADR-079 through ADR-088, because
#: canon section 24 registers no authentication, session, credential,
#: recovery or proofing code at all.
PACK14_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-14.yml"

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
#: PACK-09's one wholly new service (compliance-service). Like PACK-02
#: through PACK-06 and PACK-08 (and unlike PACK-07), PACK-09 introduces a
#: fully disjoint service directory - no existing service is extended in
#: place this round, so no "shared with an earlier pack" union is needed.
PACK09_SERVICE_DIRS: tuple[str, ...] = ("compliance-service",)
#: PACK-10's one wholly new service (finance-service). Like PACK-02
#: through PACK-06, PACK-08 and PACK-09 (and unlike PACK-07), PACK-10
#: introduces a fully disjoint service directory - no existing service is
#: extended in place this round, so no "shared with an earlier pack" union
#: is needed.
PACK10_SERVICE_DIRS: tuple[str, ...] = ("finance-service",)
#: PACK-11's one wholly new service (document-service). Like PACK-02
#: through PACK-06 and PACK-08 through PACK-10 (and unlike PACK-07),
#: PACK-11 introduces a fully disjoint service directory - no existing
#: service is extended in place this round, so no "shared with an earlier
#: pack" union is needed.
PACK11_SERVICE_DIRS: tuple[str, ...] = ("document-service",)
#: PACK-12's one wholly new service (privileged-access-service). Like
#: PACK-02 through PACK-06 and PACK-08 through PACK-11 (and unlike
#: PACK-07), PACK-12 introduces a fully disjoint service directory - no
#: existing service is extended in place this round, so no "shared with an
#: earlier pack" union is needed. The three logical bounded contexts
#: PACK-12 defines share this one directory by design (`OD-P12-04`); they
#: are separated by module, aggregate and role rather than by deployable.
PACK12_SERVICE_DIRS: tuple[str, ...] = ("privileged-access-service",)

#: PACK-13's own service directory. One wholly new service; no existing
#: PACK-02-through-PACK-12 service is extended in place this round, so
#: this scan needs no union with an earlier pack's directory list.
PACK13_SERVICE_DIRS: tuple[str, ...] = ("data-plane-service",)

#: PACK-14 adds **no** new service directory. Like PACK-07 - and unlike
#: every other pack - it extends an EXISTING service in place:
#: `identity-service`, which is already listed in `PACK02_SERVICE_DIRS`
#: and already carries PACK-02's and PACK-07's own literals. It is listed
#: here anyway, because `contracts/reason-codes/pack-14.yml` redeclares
#: every code that directory uses and is therefore a complete, standalone
#: source of truth for a scan over it. The other direction is handled the
#: way PACK-07's was: `test_reason_codes_registry.py` unions pack-14.yml
#: into pack-02's own literal-usage scan (see that file's
#: `_EXTRA_REGISTRIES_FOR_LITERAL_CHECK`), so neither pack's scan reports
#: the other pack's codes as unregistered.
PACK14_SERVICE_DIRS: tuple[str, ...] = ("identity-service",)

#: PACK-15 adds **no** new service directory either. Like PACK-07 and
#: PACK-14, it extends existing services in place: `eligibility-service`,
#: `credential-service` and `audit-core` (all already in
#: `PACK02_SERVICE_DIRS`) and `governance-service` (already in
#: `PACK05_SERVICE_DIRS`). Keeping PACK-15 inside existing workspace
#: members is deliberate - a new member would have required regenerating
#: `uv.lock`, and CI runs `uv sync --frozen` plus
#: `git diff --exit-code -- uv.lock`.
PACK15_REASON_CODES_PATH = REPO_ROOT / "contracts" / "reason-codes" / "pack-15.yml"
PACK15_SERVICE_DIRS: tuple[str, ...] = (
    "eligibility-service",
    "credential-service",
    "governance-service",
    "audit-core",
)

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
