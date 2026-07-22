"""Verifies every `reason_code` string literal actually used anywhere in
`services/*/src` is registered in `contracts/reason-codes/pack-02.yml`
(ADR-004's own stated enforcement mechanism) - a reason code must never be
free text (canon section 24).

Requires PyYAML (see `epd2_core.reason_codes`); skipped locally in this
sandbox (no network access to install PyYAML - see
`LOCAL_VERIFICATION.md`), run for real in CI.
"""

from __future__ import annotations

import re

import pytest
from _schema_helpers import REASON_CODES_PATH, SERVICES_DIR

yaml = pytest.importorskip("yaml")

_LITERAL_RE = re.compile(r'"([A-Z][A-Z0-9_]{2,})"')


def _registered_codes() -> set[str]:
    raw = yaml.safe_load(REASON_CODES_PATH.read_text(encoding="utf-8"))
    return {entry["code"] for entry in raw}


def _reason_code_like_literals_in_services() -> set[str]:
    """All-caps, underscore-containing string literals found in
    `services/*/src`. This is intentionally broad (a simple regex, not an
    AST-based "is this actually assigned to reason_code" check) so it
    catches literals used as `reason_code = "..."`, tuple elements in
    `reason_codes=(...)`, and `.append("...")` calls alike, at the cost of
    also matching any other incidental all-caps string a future change
    might introduce - a false positive here fails loudly instead of
    silently missing a real reason code.
    """
    found: set[str] = set()
    for path in SERVICES_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        for match in _LITERAL_RE.finditer(path.read_text(encoding="utf-8")):
            found.add(match.group(1))
    return found


def test_every_registry_entry_has_the_required_fields() -> None:
    raw = yaml.safe_load(REASON_CODES_PATH.read_text(encoding="utf-8"))
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
        assert not missing, f"{entry.get('code', '?')!r} missing fields: {missing}"


def test_no_duplicate_codes_in_registry() -> None:
    raw = yaml.safe_load(REASON_CODES_PATH.read_text(encoding="utf-8"))
    codes = [entry["code"] for entry in raw]
    assert len(codes) == len(set(codes)), "duplicate reason code(s) in pack-02.yml"


def test_every_reason_code_literal_used_in_services_is_registered() -> None:
    registered = _registered_codes()
    used = _reason_code_like_literals_in_services()
    missing = sorted(used - registered)
    assert not missing, (
        f"reason_code literal(s) used in services/*/src but not registered "
        f"in contracts/reason-codes/pack-02.yml: {missing}"
    )


def test_loading_the_registry_via_epd2_core_succeeds() -> None:
    from epd2_core.reason_codes import ReasonCodeRegistry

    registry = ReasonCodeRegistry.load_from_yaml(REASON_CODES_PATH)
    assert len(registry) >= 38
    assert registry.require("PERMISSION_DENIED").severity == "error"
