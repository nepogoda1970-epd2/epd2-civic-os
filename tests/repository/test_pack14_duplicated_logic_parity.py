"""PACK-14 deliberately duplicates two pieces of state across a service
boundary rather than importing them, and this file is what keeps that
honest - the same discipline
`tests/repository/test_pack07_duplicated_logic_parity.py` applies to
PACK-07's three duplications.

1. **Canon 7.2's account status list and its allowed transitions.**
   `epd2_account_service.domain.AccountStatus`/`ALLOWED_TRANSITIONS` and
   `epd2_identity_service.accounts.AccountRegistryStatus`/
   `ALLOWED_STATUS_TRANSITIONS`. A cross-service import is forbidden by
   `tests/repository/test_service_boundaries.py`, and `epd2_core`'s own
   charter forbids it holding business rules, so the values are repeated.
   **Ownership of the canonical `Account` is unchanged: it stays with
   `account-service`.**

2. **FRONT-00's ten workspaces and their origins.**
   `frontend/web-shell/foundation/workspaces.ts` is the authoritative
   declaration; `epd2_identity_service.workspaces` is the identity
   service's read of it. PACK-14 changes nothing about the
   ten-workspace / ten-origin model, and this file proves the server-side
   table still says exactly what the TypeScript one does.

3. **ADR-075's migration vocabulary.**
   `epd2_data_plane_service.migrations.MigrationClass` and
   `epd2_identity_service.persistence.MigrationKind`. The same forbidden
   import applies, so `migration_runner` reimplements the discipline;
   this file asserts that what it reimplements is a strict subset of
   what the data plane declares, classified the same way.
   **Ownership of the migration model is unchanged: it stays with
   `data-plane-service`.**

Must be run from the repository root (with PYTHONPATH covering both
services' `src/` directories, per `LOCAL_VERIFICATION.md`).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import epd2_account_service.domain as account_domain
import epd2_data_plane_service.migrations as plane_migrations
import epd2_identity_service.accounts as identity_accounts
import epd2_identity_service.migration_runner as migration_runner
import epd2_identity_service.persistence as identity_persistence
import epd2_identity_service.workspaces as identity_workspaces

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKSPACES_TS = REPO_ROOT / "frontend" / "web-shell" / "foundation" / "workspaces.ts"


# =============================================================================
# 1. Canon 7.2's account status list and transitions
# =============================================================================


def test_the_two_status_enums_carry_the_same_six_values_in_the_same_order() -> None:
    assert [status.value for status in account_domain.AccountStatus] == [
        status.value for status in identity_accounts.AccountRegistryStatus
    ]


def test_neither_enum_has_acquired_a_seventh_value() -> None:
    """`locked`, `closure_pending` and `deleted_or_anonymized` are
    represented by `AccountLock`, `AccountClosureRequest` state and a
    lifecycle outcome respectively (OD-P14-01). If either enum grows one,
    the architecture decision has been quietly reversed."""
    for enum in (account_domain.AccountStatus, identity_accounts.AccountRegistryStatus):
        assert len(enum) == 6
        values = {member.value for member in enum}
        assert "locked" not in values
        assert "closure_pending" not in values
        assert "deleted_or_anonymized" not in values


def test_the_two_allowed_transition_sets_are_identical() -> None:
    account_pairs = {
        (source.value, target.value) for source, target in account_domain.ALLOWED_TRANSITIONS
    }
    identity_pairs = {
        (source.value, target.value)
        for source, target in identity_accounts.ALLOWED_STATUS_TRANSITIONS
    }
    assert account_pairs == identity_pairs


def test_both_copies_refuse_the_same_forbidden_transitions() -> None:
    """The parity that matters operationally: every ordered pair of the
    six values behaves the same way in both copies."""
    for source in account_domain.AccountStatus:
        for target in account_domain.AccountStatus:
            account_allowed = (source, target) in account_domain.ALLOWED_TRANSITIONS
            identity_source = identity_accounts.AccountRegistryStatus(source.value)
            identity_target = identity_accounts.AccountRegistryStatus(target.value)
            identity_allowed = (
                identity_source,
                identity_target,
            ) in identity_accounts.ALLOWED_STATUS_TRANSITIONS
            assert account_allowed == identity_allowed, (
                f"{source.value} -> {target.value} differs between the two copies"
            )


def test_both_copies_parse_and_reject_the_same_status_strings() -> None:
    for member in account_domain.AccountStatus:
        assert account_domain.parse_status(member.value) is member
        assert identity_accounts.parse_account_status(member.value).value == member.value
    for unknown in ("locked", "closure_pending", "deleted_or_anonymized", ""):
        for parser in (account_domain.parse_status, identity_accounts.parse_account_status):
            try:
                parser(unknown)
            except ValueError:
                continue
            raise AssertionError(f"{parser.__name__} accepted {unknown!r}")


# =============================================================================
# 2. FRONT-00's ten workspaces
# =============================================================================


def _declared_workspaces_from_typescript() -> list[dict[str, str]]:
    """Read the id/name/origin/sensitivity tuples out of `workspaces.ts`.

    A regex rather than a parser, deliberately: the file is a literal
    array with one shape, and a parser would be a second thing to keep
    working. If the file's shape changes the regex finds nothing and the
    count assertion below fails loudly rather than silently comparing an
    empty list.
    """
    text = WORKSPACES_TS.read_text(encoding="utf-8")
    pattern = re.compile(
        r'id:\s*"(?P<id>WS-\d\d)",\s*\n\s*name:\s*"(?P<name>[^"]+)",\s*\n\s*'
        r'originPlaceholder:\s*"(?P<origin>[^"]+)",'
    )
    found = [match.groupdict() for match in pattern.finditer(text)]
    sensitivity = dict(re.findall(r'id:\s*"(WS-\d\d)"[\s\S]*?sensitivity:\s*"([^"]+)"', text))
    for entry in found:
        entry["sensitivity"] = sensitivity[entry["id"]]
    return found


def test_the_typescript_declaration_still_has_exactly_ten_workspaces() -> None:
    declared = _declared_workspaces_from_typescript()
    assert len(declared) == 10, json.dumps(declared, indent=2)


def test_every_declared_workspace_appears_in_the_identity_service_table() -> None:
    declared = {entry["id"]: entry for entry in _declared_workspaces_from_typescript()}
    server_side = {
        policy.workspace.value: policy for policy in identity_workspaces.WORKSPACE_POLICIES.values()
    }
    assert set(declared) == set(server_side)
    for workspace_id, entry in declared.items():
        policy = server_side[workspace_id]
        assert policy.origin == entry["origin"], workspace_id
        assert policy.name == entry["name"], workspace_id
        assert policy.sensitivity == entry["sensitivity"], workspace_id


def test_every_workspace_still_declares_session_sharing_forbidden() -> None:
    text = WORKSPACES_TS.read_text(encoding="utf-8")
    assert 'sessionSharing: "forbidden"' in text
    for policy in identity_workspaces.WORKSPACE_POLICIES.values():
        assert policy.session_sharing_permitted is False
        assert policy.browser_storage_identity_permitted is False


def test_the_voting_client_is_the_only_handoff_only_workspace() -> None:
    handoff_only = [
        policy.workspace.value
        for policy in identity_workspaces.WORKSPACE_POLICIES.values()
        if policy.bootstrap is identity_workspaces.BootstrapMode.HANDOFF_ONLY
    ]
    assert handoff_only == ["WS-03"]


def test_no_two_workspaces_share_an_origin() -> None:
    origins = [policy.origin for policy in identity_workspaces.WORKSPACE_POLICIES.values()]
    assert len(origins) == len(set(origins))


# =============================================================================
# 3. PACK-13's migration vocabulary
#
# `services/identity-service/migration_runner.py` reimplements ADR-075's
# discipline rather than importing `epd2_data_plane_service.migrations`,
# for the same boundary reason as section 1. `data-plane-service` remains
# the owner of the migration model; identity-service holds a strict
# subset of its change classes, and this section proves the subset has
# not drifted into a private vocabulary.
# =============================================================================


def test_every_identity_migration_kind_is_a_data_plane_migration_class() -> None:
    plane_values = {member.value for member in plane_migrations.MigrationClass}
    identity_values = {member.value for member in identity_persistence.MigrationKind}
    assert identity_values <= plane_values, (
        f"identity-service invented migration kinds: {sorted(identity_values - plane_values)}"
    )


def test_the_identity_subset_is_the_non_destructive_forward_path() -> None:
    """PACK-14's ten artefacts are additive. The subset it declares is
    expand/backfill/contract - it does not carry `switch`, `corrective`
    or `emergency`, because those classes come with controls
    (`P13-XC-003`, `P13-MIG-006`) that only the data plane implements."""
    assert {member.value for member in identity_persistence.MigrationKind} == {
        "expand",
        "backfill",
        "contract",
    }


def test_the_destructive_classification_agrees_across_both_copies() -> None:
    destructive = {member.value for member in plane_migrations.DESTRUCTIVE_MIGRATION_CLASSES}
    for member in identity_persistence.MigrationKind:
        is_destructive_here = member.value in destructive
        assert is_destructive_here == (member.value == "contract"), (
            f"{member.value} is classified differently by the two copies"
        )


def test_every_declared_pack14_migration_is_expand_and_ordered_from_one() -> None:
    """The ordering rule the runner enforces, asserted against the
    declarations themselves: contiguous sequence numbers from 1, and no
    destructive step in a pack that only creates structures."""
    sequences = [definition.sequence for definition in identity_persistence.PACK14_MIGRATIONS]
    assert sequences == list(range(1, len(sequences) + 1))
    for definition in identity_persistence.PACK14_MIGRATIONS:
        assert definition.kind is identity_persistence.MigrationKind.EXPAND, (
            f"{definition.identifier} is not additive; PACK-14 declares no destructive step"
        )


def test_each_declared_migration_has_an_artefact_on_disk() -> None:
    """The correction round's first requirement in one assertion: the
    declarations describe files that exist, not files that were
    described."""
    artefacts = migration_runner.load_artefacts()
    assert len(artefacts) == len(identity_persistence.PACK14_MIGRATIONS)
    for artefact in artefacts:
        assert artefact.path.exists()
        assert artefact.path.suffix == ".sql"
        assert artefact.path.read_text(encoding="utf-8").strip()
