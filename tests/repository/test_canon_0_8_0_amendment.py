"""Repository-level test: the PACK-10 canon 0.8.0 amendment, and the
state the PACK-10 implementation round left it in.

This is a documentation-and-version check, not a business-behaviour
check. The 0.8.0 canon round amended
`docs/canonical/TZ-00-domain-event-canon.md` with the party-finance
bounded context (section 19f, event subsection 20.17, and the new entries
in sections 22, 23 and 24) and shipped no runtime code.

The PACK-10 implementation round is the round canon 19f.25's
implementation gate was waiting for, so three of these assertions were
inverted with it rather than left asserting the previous round's state:
`REPOSITORY_VERSION` is now 0.10.0, the finance context is declared
`reference_implementation`, and `services/finance-service` must exist,
carry its twelve modules and offer no deletion method. What did **not**
change is the canon itself - `CANON_VERSION` stays 0.8.0 and the canon
text is untouched - and the boundary: no shared finance package, no
finance frontend, no second finance-named service.

Each test below asserts that the corresponding check in
`scripts/check_canon_0_8_0.py` reports no problem.

Must be run from the repository root (see docs/development/local-development.md).
"""

from scripts.check_canon_0_8_0 import (
    REPO_ROOT,
    check_adr_registry_integrity,
    check_adr_set_unchanged,
    check_canon_version_declared,
    check_cross_pack_ownership_unchanged,
    check_finance_auditor_incompatibility,
    check_finance_context_present,
    check_finance_entity_ownership,
    check_finance_event_catalogue,
    check_finance_implementation_status,
    check_finance_party_handle_not_global_identity,
    check_finance_runtime_within_boundary,
    check_finance_voting_links_forbidden,
    check_ledger_immutability_and_balancing,
    check_reason_code_registry,
    check_report_submission_distinct_from_acceptance,
    check_repository_compatibility,
    check_repository_version_unchanged,
    find_problems,
)


def test_canon_version_is_declared_as_0_8_0() -> None:
    problems = check_canon_version_declared(REPO_ROOT)
    assert problems == [], f"Canon version problems: {problems}"


def test_repository_version_is_the_one_this_round_is_entitled_to() -> None:
    problems = check_repository_version_unchanged(REPO_ROOT)
    assert problems == [], f"Repository version problems: {problems}"


def test_repository_compatibility_accepts_current_repository() -> None:
    problems = check_repository_compatibility(REPO_ROOT)
    assert problems == [], f"Compatibility metadata problems: {problems}"


def test_finance_context_is_declared_a_reference_implementation() -> None:
    problems = check_finance_implementation_status(REPO_ROOT)
    assert problems == [], f"Implementation status problems: {problems}"


def test_the_finance_runtime_exists_and_stays_inside_its_boundary() -> None:
    problems = check_finance_runtime_within_boundary(REPO_ROOT)
    assert problems == [], f"Finance implementation problems: {problems}"


def test_finance_bounded_context_is_present_in_canon() -> None:
    problems = check_finance_context_present(REPO_ROOT)
    assert problems == [], f"Finance context problems: {problems}"


def test_every_finance_aggregate_has_an_ownership_row() -> None:
    problems = check_finance_entity_ownership(REPO_ROOT)
    assert problems == [], f"Finance ownership problems: {problems}"


def test_finance_party_handle_is_not_a_global_identity() -> None:
    problems = check_finance_party_handle_not_global_identity(REPO_ROOT)
    assert problems == [], f"Global identity problems: {problems}"


def test_finance_to_voting_links_are_forbidden() -> None:
    problems = check_finance_voting_links_forbidden(REPO_ROOT)
    assert problems == [], f"Forbidden link problems: {problems}"


def test_ledger_balances_and_posted_entries_are_immutable() -> None:
    problems = check_ledger_immutability_and_balancing(REPO_ROOT)
    assert problems == [], f"Ledger rule problems: {problems}"


def test_finance_auditor_incompatibility_is_registered() -> None:
    problems = check_finance_auditor_incompatibility(REPO_ROOT)
    assert problems == [], f"Incompatibility problems: {problems}"


def test_report_submission_is_distinct_from_acceptance() -> None:
    problems = check_report_submission_distinct_from_acceptance(REPO_ROOT)
    assert problems == [], f"Report lifecycle problems: {problems}"


def test_cross_pack_ownership_is_unchanged() -> None:
    problems = check_cross_pack_ownership_unchanged(REPO_ROOT)
    assert problems == [], f"Cross-pack ownership problems: {problems}"


def test_finance_event_catalogue_is_governed() -> None:
    problems = check_finance_event_catalogue(REPO_ROOT)
    assert problems == [], f"Event catalogue problems: {problems}"


def test_reason_codes_are_unique_and_complete() -> None:
    problems = check_reason_code_registry(REPO_ROOT)
    assert problems == [], f"Reason code problems: {problems}"


def test_no_accepted_adr_was_rewritten() -> None:
    problems = check_adr_set_unchanged(REPO_ROOT)
    assert problems == [], f"ADR problems: {problems}"


def test_canon_0_8_0_amendment_has_no_problems() -> None:
    problems = find_problems(REPO_ROOT)
    assert problems == [], f"Canon 0.8.0 amendment problems: {problems}"


def test_adr_registry_ids_are_unique_and_match_their_titles() -> None:
    problems = check_adr_registry_integrity(REPO_ROOT)
    assert problems == [], f"ADR registry integrity problems: {problems}"
