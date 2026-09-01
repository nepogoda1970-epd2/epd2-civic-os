"""Verifies every `reason_code` string literal actually used anywhere in
a pack's own `services/*/src` is registered in that pack's own
`contracts/reason-codes/*.yml` (ADR-004's own stated enforcement
mechanism) - a reason code must never be free text (canon section 24).

Parametrized over every implementation pack (PACK-02 through PACK-09):
each scan
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
    PACK05_REASON_CODES_PATH,
    PACK05_SERVICE_DIRS,
    PACK06_REASON_CODES_PATH,
    PACK06_SERVICE_DIRS,
    PACK07_REASON_CODES_PATH,
    PACK07_SERVICE_DIRS,
    PACK08_REASON_CODES_PATH,
    PACK08_SERVICE_DIRS,
    PACK09_REASON_CODES_PATH,
    PACK09_SERVICE_DIRS,
    PACK10_REASON_CODES_PATH,
    PACK10_SERVICE_DIRS,
    PACK11_REASON_CODES_PATH,
    PACK11_SERVICE_DIRS,
    PACK12_REASON_CODES_PATH,
    PACK12_SERVICE_DIRS,
    PACK13_REASON_CODES_PATH,
    PACK13_SERVICE_DIRS,
    PACK14_REASON_CODES_PATH,
    PACK14_SERVICE_DIRS,
    PACK15_REASON_CODES_PATH,
    PACK15_SERVICE_DIRS,
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
    ("pack-05", PACK05_REASON_CODES_PATH, PACK05_SERVICE_DIRS, 25),
    ("pack-06", PACK06_REASON_CODES_PATH, PACK06_SERVICE_DIRS, 22),
    ("pack-07", PACK07_REASON_CODES_PATH, PACK07_SERVICE_DIRS, 38),
    ("pack-08", PACK08_REASON_CODES_PATH, PACK08_SERVICE_DIRS, 32),
    ("pack-09", PACK09_REASON_CODES_PATH, PACK09_SERVICE_DIRS, 40),
    ("pack-10", PACK10_REASON_CODES_PATH, PACK10_SERVICE_DIRS, 90),
    ("pack-11", PACK11_REASON_CODES_PATH, PACK11_SERVICE_DIRS, 71),
    ("pack-12", PACK12_REASON_CODES_PATH, PACK12_SERVICE_DIRS, 141),
    ("pack-13", PACK13_REASON_CODES_PATH, PACK13_SERVICE_DIRS, 125),
    ("pack-14", PACK14_REASON_CODES_PATH, PACK14_SERVICE_DIRS, 202),
    ("pack-15", PACK15_REASON_CODES_PATH, PACK15_SERVICE_DIRS, 84),
)
_PACK_IDS = [pack_name for pack_name, _, _, _ in _PACKS]

#: PACK-07 (canon-0.6.0, ADR-026 through ADR-031) is the first pack that
#: does NOT introduce a wholly disjoint set of service directories: it
#: also extends two existing PACK-02 services (identity-service,
#: eligibility-service) in place, so those two directories' `src/` trees
#: now mix genuinely-PACK-02 and genuinely-PACK-07 reason-code literals
#: together. For pack-02's own literal-usage check only, this maps
#: "pack-02" to the additional registry file(s) that must be unioned in
#: before computing "used but not registered" - never for the other three
#: checks (required-fields/no-duplicates/loads-via-epd2-core), which
#: still validate pack-02.yml as its own, independently well-formed file.
_EXTRA_REGISTRIES_FOR_LITERAL_CHECK: dict[str, tuple[Path, ...]] = {
    "pack-02": (
        PACK07_REASON_CODES_PATH,
        PACK14_REASON_CODES_PATH,
        PACK15_REASON_CODES_PATH,
    ),
    # PACK-15 extends `governance-service` (PACK-05's directory) with the
    # Voting Context Registry, so pack-05's own literal scan must union
    # pack-15.yml - the same mechanism PACK-07 and PACK-14 already use for
    # the PACK-02 directories above.
    "pack-05": (PACK15_REASON_CODES_PATH,),
    # PACK-15's own scan covers four directories that already carry
    # PACK-02 through PACK-14 literals, so every earlier registry is
    # unioned in before computing "used but not registered". This is the
    # inverse of the rows above and exists for the same reason: a scan
    # scoped to one pack must not fail on another pack's codes.
    "pack-15": (
        REASON_CODES_PATH,
        PACK03_REASON_CODES_PATH,
        PACK04_REASON_CODES_PATH,
        PACK05_REASON_CODES_PATH,
        PACK06_REASON_CODES_PATH,
        PACK07_REASON_CODES_PATH,
        PACK08_REASON_CODES_PATH,
        PACK09_REASON_CODES_PATH,
        PACK10_REASON_CODES_PATH,
        PACK11_REASON_CODES_PATH,
        PACK12_REASON_CODES_PATH,
        PACK13_REASON_CODES_PATH,
        PACK14_REASON_CODES_PATH,
    ),
}

#: All-caps literals that the deliberately broad regex above matches but
#: that are provably not reason codes, enumerated per pack.
#:
#: The scan's own docstring says a false positive should "fail loudly
#: instead of silently missing a real reason code" - and it did. The
#: honest response to a loud false positive is to name the exact string
#: and say why it is not a code, not to narrow the pattern: a narrower
#: regex would also stop catching whole families of genuine codes.
#:
#: `EUR` is an ISO 4217 currency code in
#: `epd2_finance_service.domain.GOVERNED_CURRENCIES` and
#: `CURRENCY_SCALE`. It is three characters, all upper case, and so
#: matches `[A-Z][A-Z0-9_]{2,}`; it is not a `reason_code` and could not
#: be registered as one without putting a currency in the refusal
#: registry. Enumerated exactly rather than excluded by a rule such as
#: "no underscore, therefore not a code", because such a rule would also
#: hide any future genuine single-word code.
#: PACK-11's five are `__all__` entries and module-level constant names -
#: `epd2_document_service.application.__all__` re-exports
#: `AUDIT_POLICY_VERSION`, and `epd2_document_service.__init__.__all__`
#: re-exports `CANON_VERSION`, `REPOSITORY_VERSION`,
#: `DOCUMENT_CONTEXT_IMPLEMENTATION_STATUS` and
#: `IMPLEMENTED_FIR_ENTRIES`. Each is an upper-case *name in a string*,
#: which is exactly the shape the broad regex is designed to catch, and
#: none is a reason code. Enumerated exactly, per this file's own rule:
#: excluding them by a heuristic such as "appears inside `__all__`" would
#: also hide a genuine code that a future `__all__` happened to mention.
_NON_REASON_CODE_LITERALS: dict[str, frozenset[str]] = {
    #: PACK-02's own scan covers `identity-service`, which PACK-14 extends
    #: in place, so the ten literals PACK-14 contributes to that directory
    #: are false positives for pack-02's scan too. They are the same ten
    #: enumerated under "pack-14" below - five `__init__` constant names,
    #: three `ConfidentialityClass` values and two workspace sensitivity
    #: strings - and they are repeated here rather than derived from that
    #: entry, because an allowlist that quietly inherits from another
    #: pack's is an allowlist nobody can read.
    "pack-02": frozenset(
        {
            "CANDIDATE_FIR_ENTRIES",
            "CANON_VERSION",
            "COMMIT",
            "CONFIDENTIAL",
            "FINANCIAL_CONFIDENTIAL",
            "IDENTITY_CONTEXT_IMPLEMENTATION_STATUS",
            "IMPLEMENTED_FIR_ENTRIES",
            "INTERNAL",
            "PUBLIC_APPROVED",
            "REPOSITORY_VERSION",
            "RESTRICTED",
            "ROLLBACK",
        }
    ),
    "pack-10": frozenset({"EUR"}),
    "pack-11": frozenset(
        {
            "AUDIT_POLICY_VERSION",
            "CANON_VERSION",
            "DOCUMENT_CONTEXT_IMPLEMENTATION_STATUS",
            "IMPLEMENTED_FIR_ENTRIES",
            "REPOSITORY_VERSION",
        }
    ),
    #: PACK-12's are the same shape as PACK-11's - `__all__` entries and
    #: module-level constant names, each an upper-case *name in a string*,
    #: none a reason code. Enumerated exactly for the same reason: a
    #: heuristic such as "appears inside `__all__`" would also hide a
    #: genuine code that a future `__all__` happened to mention.
    "pack-12": frozenset(
        {
            "CANON_VERSION",
            "IMPLEMENTED_FIR_ENTRIES",
            "PRIVILEGED_ACCESS_CONTEXT_IMPLEMENTATION_STATUS",
            "REPOSITORY_VERSION",
        }
    ),
    #: PACK-13's five are the same shape again - `__all__` entries in
    #: `epd2_data_plane_service.__init__`, each an upper-case *name in a
    #: string*, none a reason code. `CANDIDATE_FIR_ENTRIES` is the one
    #: new shape: it names the FIR entry this round leaves at candidate
    #: status, and it is a constant name rather than a refusal.
    #: Enumerated exactly for the same reason as PACK-11's and
    #: PACK-12's: a heuristic such as "appears inside `__all__`" would
    #: also hide a genuine code that a future `__all__` happened to
    #: mention.
    "pack-13": frozenset(
        {
            "CANDIDATE_FIR_ENTRIES",
            "CANON_VERSION",
            "DATA_PLANE_CONTEXT_IMPLEMENTATION_STATUS",
            "IMPLEMENTED_FIR_ENTRIES",
            "REPOSITORY_VERSION",
        }
    ),
    #: PACK-14's five `__init__` constant names are the same shape as
    #: PACK-11's through PACK-13's. `COMMIT` and `ROLLBACK` are SQL verbs
    #: in the statement strings
    #: `epd2_identity_service.migration_runner` executes to open and
    #: close a migration transaction; they are keywords of another
    #: language that happen to be upper case, and registering them would
    #: put SQL in the refusal registry. The four remaining entries are a
    #: new shape and are enumerated for the same reason rather than
    #: excluded by a rule: `INTERNAL`, `CONFIDENTIAL` and `RESTRICTED` are the
    #: values of `epd2_identity_service.forms.ConfidentialityClass` (the
    #: form inventory's confidentiality column), and `PUBLIC_APPROVED`
    #: and `FINANCIAL_CONFIDENTIAL` are two of the sensitivity strings
    #: `epd2_identity_service.workspaces` copies verbatim from
    #: `frontend/web-shell/foundation/workspaces.ts`. Each is an
    #: upper-case *classification value*, not a refusal, and none could
    #: be registered as a reason code without putting a confidentiality
    #: class in the refusal registry. Enumerated exactly rather than
    #: excluded by a rule such as "no underscore, therefore not a code",
    #: because such a rule would also hide a future genuine single-word
    #: code.
    "pack-14": frozenset(
        {
            "CANDIDATE_FIR_ENTRIES",
            "CANON_VERSION",
            "COMMIT",
            "CONFIDENTIAL",
            "FINANCIAL_CONFIDENTIAL",
            "IDENTITY_CONTEXT_IMPLEMENTATION_STATUS",
            "IMPLEMENTED_FIR_ENTRIES",
            "INTERNAL",
            "ROLLBACK",
            "PUBLIC_APPROVED",
            "REPOSITORY_VERSION",
            "RESTRICTED",
        }
    ),
}


#: Directory names under a service's `src/` whose reason-code-shaped
#: literals belong to a different catalogue and must not be scanned here.
#:
#: There is exactly one, and it is scoped by **path** rather than by listing
#: its ~65 literals in `_NON_REASON_CODE_LITERALS`, because those literals
#: *are* genuine refusal codes — they are simply not this registry's.
#:
#: `services/voting-service/src/epd2_voting_service/reference/` is the
#: PACK-16D **reference implementation**. It is not a production service
#: path: it authenticates nobody, is reachable from no endpoint, and its
#: package banner says so. Its codes are the refusals of an executable
#: model of the PACK-16A/16B/16C specification, and they are catalogued in
#: `docs/packs/PACK-16/PACK-16D-REASON-CODE-COVERAGE.md`, which is asserted
#: against the code by that pack's own tests.
#:
#: Registering them in `contracts/reason-codes/pack-03.yml` instead would be
#: worse than leaving them out: that file is the voting service's **public
#: contract**, and putting `EPD2_VOTING_REFERENCE_TEST_PROFILE` or
#: `CRYPTO_TEST_MODE_REACHABLE` in it would tell a client to expect refusals
#: the deployed service can never emit.
#:
#: This exclusion was added when PyYAML became installable in the build
#: environment and this test ran for the first time since PACK-16D landed.
#: It had been **skipping**, not passing — which is why the mismatch went
#: unnoticed through two candidate rounds, and is worth remembering the next
#: time a skipped test looks harmless.
_EXCLUDED_SUBTREES: frozenset[str] = frozenset({"reference"})


def _registered_codes(registry_path: Path) -> set[str]:
    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    return {entry["code"] for entry in raw}


def _reason_code_like_literals_in(pack_name: str, service_dir_names: tuple[str, ...]) -> set[str]:
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
    - **The PACK-16D reference implementation subtree is excluded**, by
      path, for the reason stated at `_EXCLUDED_SUBTREES` below.
    """
    found: set[str] = set()
    for service_dir_name in service_dir_names:
        src_dir = SERVICES_DIR / service_dir_name / "src"
        for path in src_dir.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            if any(part in _EXCLUDED_SUBTREES for part in path.parts):
                continue
            for match in _LITERAL_RE.finditer(path.read_text(encoding="utf-8")):
                found.add(match.group(1))
    return found - _NON_REASON_CODE_LITERALS.get(pack_name, frozenset())


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
    for extra_registry_path in _EXTRA_REGISTRIES_FOR_LITERAL_CHECK.get(pack_name, ()):
        registered |= _registered_codes(extra_registry_path)
    used = _reason_code_like_literals_in(pack_name, service_dir_names)
    missing = sorted(used - registered)
    assert not missing, (
        f"reason_code literal(s) used in {pack_name}'s services/*/src but not registered "
        f"in {registry_path.name}"
        + (
            f" (nor in {', '.join(p.name for p in _EXTRA_REGISTRIES_FOR_LITERAL_CHECK[pack_name])})"
            if pack_name in _EXTRA_REGISTRIES_FOR_LITERAL_CHECK
            else ""
        )
        + f": {missing}"
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
