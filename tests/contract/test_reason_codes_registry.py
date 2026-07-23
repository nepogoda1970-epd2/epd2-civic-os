"""Verifies every `reason_code` string literal actually used anywhere in
a pack's own `services/*/src` is registered in that pack's own
`contracts/reason-codes/*.yml` (ADR-004's own stated enforcement
mechanism) - a reason code must never be free text (canon section 24).

Parametrized over all three packs (PACK-02, PACK-03, PACK-04): each scan
is scoped to only that pack's own service directories
(`PACK02_SERVICE_DIRS`/`PACK03_SERVICE_DIRS`/`PACK04_SERVICE_DIRS`),
checked against only that pack's own registry file. `services/*` now
contains all twelve services from three packs - scanning the whole tree
against a single pack's registry would spuriously fail once another
pack's services exist, since every service uses its own additive reason
codes never registered in another pack's file. This file existed
pre-PACK-03 scoped only to PACK-02 (a bare, unparametrized scan of the
whole `services/` tree against `pack-02.yml` only); the PACK-03
parametrization/scoping added a second pack, and this PACK-04 update adds
a third.

Requires PyYAML (see `epd2_core.reason_codes`); skipped locally in this
sandbox (no network access to install PyYAML - see
`LOCAL_VERIFICATION.md`), run for real in CI.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from _schema_helpers import (
    PACK02_SERVICE_DIRS,
    PACK03_REASON_CODES_PATH,
    PACK03_SERVICE_DIRS,
    PACK04_REASON_CODES_PATH,
    PACK04_SERVICE_DIRS,
    REASON_CODES_PATH,
    SERVICES_DIR,
)

yaml = pytest.importorskip("yaml")

_LITERAL_RE = re.compile(r'"([A-Z][A-Z0-9_]{2,})"')

#: (pack_name, registry_path, service_dir_names, minimum_registry_size)
#: per pack - the single source of truth every parametrized test below
#: iterates. PACK-02's own tuple is unchanged from before this file's
#: PACK-03 extension (same registry path, same service list, same
#: minimum-size assertion of >= 38).
_PACKS: tuple[tuple[str, Path, tuple[str, ...], int], ...] = (
    ("pack-02", REASON_CODES_PATH, PACK02_SERVICE_DIRS, 38),
    ("pack-03", PACK03_REASON_CODES_PATH, PACK03_SERVICE_DIRS, 60),
    ("pack-04", PACK04_REASON_CODES_PATH, PACK04_SERVICE_DIRS, 18),
)
_PACK_IDS = [pack_name for pack_name, _, _, _ in _PACKS]


def _registered_codes(registry_path: Path) -> set[str]:
    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    return {entry["code"] for entry in raw}


def _reason_code_like_literals_in(service_dir_names: tuple[str, ...]) -> set[str]:
    """All-caps, underscore-containing string literals found only in the
    given pack's own service directories' `src/` trees - intentionally
    broad (a simple regex, not an AST-based "is this actually assigned to
    reason_code" check) so it catches literals used as
    `reason_code = "..."`, tuple elements in `reason_codes=(...)`, and
    `.append("...")` calls alike, at the cost of also matching any other
    incidental all-caps string a future change might introduce - a false
    positive here fails loudly instead of silently missing a real reason
    code.

    Scoped two ways, both load-bearing:

    - Per-pack (not `SERVICES_DIR.rglob("*.py")` over the whole tree) so
      this pack's scan never sees the other pack's own additive codes at
      all - the critical fix this file needed once PACK-03's six services
      exist alongside PACK-02's five under the same `services/` directory.
    - `src/` only, not each service's own `tests/` directory - a service's
      *test* file may legitimately contain an all-caps quoted literal that
      is not a reason code at all (e.g.
      `services/voting-service/tests/test_application.py` asserts
      `"INVALIDATED" not in source` as a *structural* regression check,
      per ADR-009 item 14 - `"INVALIDATED"` there is a substring being
      searched for, not a `reason_code` value ever produced by this
      service). Reason codes are used and defined in a service's `src/`,
      never in its own test assertions about source text.
    """
    found: set[str] = set()
    for service_dir_name in service_dir_names:
        src_dir = SERVICES_DIR / service_dir_name / "src"
        for path in src_dir.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            for match in _LITERAL_RE.finditer(path.read_text(encoding="utf-8")):
                found.add(match.group(1))
    return found


@pytest.mark.parametrize(
    "pack_name,registry_path,service_dir_names,minimum_size", _PACKS, ids=_PACK_IDS
)
def test_every_registry_entry_has_the_required_fields(
    pack_name: str,
    registry_path: Path,
    service_dir_names: tuple[str, ...],
    minimum_size: int,
) -> None:
    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    required = {
        "code",
        "meaning",
        "severity",
        "description",
        "retryable",
        "owner",
        "introduced_in_version",
    }
    for entry in raw:
        missing = required - set(entry)
        assert not missing, f"{pack_name} {entry.get('code', '?')!r} missing fields: {missing}"


@pytest.mark.parametrize(
    "pack_name,registry_path,service_dir_names,minimum_size", _PACKS, ids=_PACK_IDS
)
def test_no_duplicate_codes_in_registry(
    pack_name: str,
    registry_path: Path,
    service_dir_names: tuple[str, ...],
    minimum_size: int,
) -> None:
    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    codes = [entry["code"] for entry in raw]
    assert len(codes) == len(set(codes)), f"duplicate reason code(s) in {registry_path.name}"


@pytest.mark.parametrize(
    "pack_name,registry_path,service_dir_names,minimum_size", _PACKS, ids=_PACK_IDS
)
def test_every_reason_code_literal_used_in_services_is_registered(
    pack_name: str,
    registry_path: Path,
    service_dir_names: tuple[str, ...],
    minimum_size: int,
) -> None:
    registered = _registered_codes(registry_path)
    used = _reason_code_like_literals_in(service_dir_names)
    missing = sorted(used - registered)
    assert not missing, (
        f"reason_code literal(s) used in {pack_name}'s services/*/src but not registered "
        f"in {registry_path.name}: {missing}"
    )


@pytest.mark.parametrize(
    "pack_name,registry_path,service_dir_names,minimum_size", _PACKS, ids=_PACK_IDS
)
def test_loading_the_registry_via_epd2_core_succeeds(
    pack_name: str,
    registry_path: Path,
    service_dir_names: tuple[str, ...],
    minimum_size: int,
) -> None:
    from epd2_core.reason_codes import ReasonCodeRegistry

    registry = ReasonCodeRegistry.load_from_yaml(registry_path)
    assert len(registry) >= minimum_size
    assert registry.require("PERMISSION_DENIED").severity == "error"
