"""Repository-level test: forbidden files and directories must be absent.

Must be run from the repository root (see docs/development/local-development.md).
"""

from scripts.check_forbidden_files import (
    REPO_ROOT,
    _is_forbidden_identity_link_filename,
    find_forbidden_paths,
)


def test_no_forbidden_paths_present() -> None:
    forbidden = find_forbidden_paths(REPO_ROOT)
    assert forbidden == [], f"Forbidden paths found: {forbidden}"


def test_identity_participation_mapping_filenames_are_flagged() -> None:
    """CLAUDE-PACK-02 section 15: a filename naming an identity/person
    entity together with a credential/participation/account entity AND an
    explicit map/link/join word must be flagged as a forbidden central
    identity-participation mapping table/file."""
    for bad_name in (
        "identity_credential_map.py",
        "person_participation_link.json",
        "identity_account_mapping.sql",
        "credential_identity_join.csv",
    ):
        assert _is_forbidden_identity_link_filename(bad_name), bad_name


def test_legitimate_domain_filenames_are_not_flagged() -> None:
    """Filenames that merely mention two domain nouns without a link/map
    word must not be flagged - this is the real PACK-02 schema/service
    file set, not a mapping table."""
    for real_name in (
        "participation-credential.schema.json",
        "identity-record.schema.json",
        "identity-event-payload.v1.schema.json",
        "credential-issued-or-revoked-payload.v1.schema.json",
        "account.schema.json",
    ):
        assert not _is_forbidden_identity_link_filename(real_name), real_name
