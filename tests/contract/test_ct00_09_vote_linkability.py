"""CT-00-09 Vote Linkability (canon section 27): an ordinary administrator
cannot obtain an account ID from a `VoteEnvelope`.

Per pack section 12.1, CT-00-09 is in scope for PACK-02 only as a
*structural future-safety test*: `Ballot`/`VoteEnvelope`/voting are out of
scope for this pack (pack section 3.2), so there is no `VoteEnvelope` to
exercise directly. What PACK-02 *can* and must guarantee now is that its
own `ParticipationCredential` - the artifact a future Voting pack would
build `VoteEnvelope` on top of - carries no identity linkage, so that
guarantee doesn't have to be retrofitted later under time pressure.
"""

from __future__ import annotations

import ast
import inspect
import json
from datetime import timedelta
from pathlib import Path
from uuid import UUID, uuid4

from _schema_helpers import to_jsonable

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.application import issue_participation_credential
from epd2_credential_service.domain import (
    FORBIDDEN_FIELD_NAMES,
    CredentialType,
    ParticipationCredential,
)
from epd2_credential_service.storage import InMemoryCredentialStore
from epd2_eligibility_service.application import (
    create_eligibility_rule,
    create_eligibility_snapshot,
)
from epd2_eligibility_service.storage import (
    InMemoryEligibilityRuleStore,
    InMemoryEligibilitySnapshotStore,
)
from epd2_voting_service.application import (
    approve_ballot_configuration,
    cast_vote,
    create_ballot,
    open_ballot,
    submit_ballot_for_configuration_review,
)
from epd2_voting_service.domain import (
    FORBIDDEN_FIELD_NAMES as VOTE_FORBIDDEN,
)
from epd2_voting_service.domain import (
    BallotMethod,
    VoteEnvelope,
)
from epd2_voting_service.storage import (
    InMemoryBallotOptionStore,
    InMemoryBallotStore,
    InMemoryVoteEnvelopeStore,
)


def test_participation_credential_has_no_account_or_identity_linkage_field() -> None:
    """No field on `ParticipationCredential` could ever resolve to an
    `Account`/`IdentityRecord` - the structural precondition a future
    Voting pack's own CT-00-09 test will depend on."""
    field_names = set(ParticipationCredential.__dataclass_fields__)
    assert not (field_names & FORBIDDEN_FIELD_NAMES)
    assert "account_id" not in field_names
    assert "identity_record_id" not in field_names


def _identifier_field_names(dataclass: type) -> set[str]:
    """The subset of a dataclass's field names that look like identifiers
    (join keys) rather than incidental same-named value fields (e.g. both
    `ParticipationCredential` and `IdentityRecord` happen to have an
    `expires_at` datetime field - that is not a linkage, since neither
    value ever refers to the other's row)."""
    return {
        name
        for name in dataclass.__dataclass_fields__  # type: ignore[attr-defined]
        if name.endswith("_id")
    }


def test_credential_shares_no_join_key_with_account_or_identity_record() -> None:
    """A `ParticipationCredential` and an `Account`/`IdentityRecord` share
    no *identifier* field that could serve as a join key linking them
    together - the only identifier fields a credential exposes are its
    own `credential_id` and `scope_id` (a civic-space/process reference,
    never a person/account/identity reference), neither of which appears
    on `Account` or `IdentityRecord` at all. (Non-identifier fields may
    coincidentally share a name, e.g. `expires_at` on both a credential
    and an identity record - that is not a linkage.)"""
    from epd2_account_service.domain import Account
    from epd2_identity_service.domain import IdentityRecord

    credential_ids = _identifier_field_names(ParticipationCredential)
    account_ids = _identifier_field_names(Account)
    identity_ids = _identifier_field_names(IdentityRecord)

    assert credential_ids == {"credential_id", "scope_id"}
    assert credential_ids & account_ids == set()
    assert credential_ids & identity_ids == set()


# =============================================================================
# PACK-03: voting is now in scope, so CT-00-09 can (and must) be exercised
# directly against a real `VoteEnvelope`, not just the PACK-02 structural
# future-safety proxy above.
# =============================================================================


def test_vote_envelope_dataclass_has_no_forbidden_identity_fields() -> None:
    field_names = set(VoteEnvelope.__dataclass_fields__)
    assert not (field_names & VOTE_FORBIDDEN)


def test_vote_envelope_credential_proof_is_a_bare_uuid_reference() -> None:
    """`credential_proof` is typed as a bare `UUID` (an opaque credential
    reference), never a structured identity object or account/identity
    field name."""
    annotation = VoteEnvelope.__dataclass_fields__["credential_proof"].type
    assert annotation in ("UUID", UUID) or "UUID" in str(annotation)
    assert "account_id" not in VoteEnvelope.__dataclass_fields__
    assert "identity_record_id" not in VoteEnvelope.__dataclass_fields__


def test_real_cast_vote_event_payload_has_no_identity_fields(
    ballot_store: InMemoryBallotStore,
    ballot_option_store: InMemoryBallotOptionStore,
    vote_envelope_store: InMemoryVoteEnvelopeStore,
    audit_store: InMemoryAuditEventStore,
    credential_store: InMemoryCredentialStore,
    eligibility_rule_store: InMemoryEligibilityRuleStore,
    eligibility_snapshot_store: InMemoryEligibilitySnapshotStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """A real, end-to-end `cast_vote` call's emitted event payload -
    round-tripped through JSON exactly as a wire consumer would see it -
    contains none of `FORBIDDEN_FIELD_NAMES`, proving the guarantee is
    real at the actual emission boundary, not just at the dataclass
    definition checked above."""
    rule = create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=uuid4(),
        rule_version=1,
        scope_type="ballot",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=clock.now(),
        valid_until=None,
    )
    snapshot = create_eligibility_snapshot(
        eligibility_snapshot_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        eligible_decisions=(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=clock,
    ).snapshot

    ballot_id = uuid4()
    credential = issue_participation_credential(
        credential_store,
        audit_store,
        credential_id=uuid4(),
        credential_type=CredentialType.BALLOT_ACCESS,
        scope_type="ballot",
        scope_id=ballot_id,
        valid_from=clock.now(),
        expires_at=clock.now() + timedelta(days=365),
        usage_limit=None,
        rule_version=1,
        eligibility_snapshot_digest=snapshot.digest,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    ).credential

    creator = ActorRef(actor_id=uuid4(), actor_type="service")
    create_ballot(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        space_id=uuid4(),
        subject_type="initiative",
        subject_id=uuid4(),
        question="Shall this pass?",
        ballot_method=BallotMethod.YES_NO,
        secrecy_mode="secret",
        eligibility_rule_version=1,
        delegation_policy_version=1,
        quorum_rule="none",
        threshold_rule="simple_majority",
        opens_at=clock.now(),
        closes_at=clock.now() + timedelta(days=1),
        challenge_window_hours=None,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    submit_ballot_for_configuration_review(
        ballot_store,
        audit_store,
        eligibility_snapshot_store,
        ballot_id=ballot_id,
        eligibility_snapshot_id=snapshot.eligibility_snapshot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    approve_ballot_configuration(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    open_ballot(
        ballot_store,
        ballot_option_store,
        audit_store,
        ballot_id=ballot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    result = cast_vote(
        ballot_store,
        vote_envelope_store,
        audit_store,
        credential_store,
        vote_envelope_id=uuid4(),
        ballot_id=ballot_id,
        credential_proof=credential.credential_id,
        encrypted_or_encoded_choice="yes",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    payload_text = json.dumps(to_jsonable(result.event.payload))
    for forbidden in VOTE_FORBIDDEN:
        assert forbidden not in payload_text


# =============================================================================
# PACK-04 (transparency-service): canon section 19a/ADR-013's own explicit
# prohibition - no vote-envelope or delegation-graph data may ever reach a
# public Transparency artifact. Unlike PACK-03 above, transparency-service
# never imports `epd2_voting_service.domain.VoteEnvelope` or
# `epd2_delegation_service` at all (ADR-012's exclusion list), so this
# section checks the boundary from the *outside*: (1) the pack's own
# `FORBIDDEN_FIELD_NAMES` names the exact vote-linkability fields a caller
# could otherwise smuggle into `raw_content`, (2) a real end-to-end command
# call proves those fields are dropped from the persisted content and the
# emitted public payload even when a caller supplies them, and (3) an
# AST-based import scan (mirroring
# `test_voting_service_never_imports_account_or_identity_service` above)
# confirms no module in `epd2_transparency_service` ever imports
# `epd2_delegation_service` or `epd2_voting_service.domain`'s
# `VoteEnvelope`-carrying module directly.
# =============================================================================


def test_transparency_forbidden_fields_names_the_vote_linkability_fields() -> None:
    """`epd2_transparency_service.domain.FORBIDDEN_FIELD_NAMES` must name
    every vote-envelope/credential-linkage field a caller could otherwise
    smuggle into a `PublicLedgerEntry`'s `raw_content` (canon section
    19a.5/19a.6 - "no ... vote-envelope/delegation-graph ... data in
    public output")."""
    from epd2_transparency_service.domain import FORBIDDEN_FIELD_NAMES as TRANSPARENCY_FORBIDDEN

    assert {"vote_envelope_id", "encrypted_or_encoded_choice", "credential_proof"} <= (
        TRANSPARENCY_FORBIDDEN
    )


def test_real_publish_ledger_entry_drops_vote_linkability_fields_from_public_output() -> None:
    """A real, end-to-end `publish_ledger_entry` call whose caller-supplied
    `raw_content` includes vote-envelope-shaped keys - proving the
    guarantee holds at the actual persistence/emission boundary, not just
    at the `FORBIDDEN_FIELD_NAMES` definition checked above."""
    from datetime import UTC as _UTC
    from datetime import datetime as _datetime

    from epd2_audit_core.storage import InMemoryAuditEventStore as _AuditStore
    from epd2_core.clock import FixedClock as _FixedClock
    from epd2_core.event_envelope import ActorRef as _ActorRef
    from epd2_transparency_service.application import (
        activate_disclosure_policy,
        define_disclosure_policy,
        publish_ledger_entry,
    )
    from epd2_transparency_service.domain import (
        DisclosureClass,
        FieldRule,
        LedgerSubjectType,
        Transformation,
    )
    from epd2_transparency_service.storage import (
        InMemoryDisclosurePolicyStore,
        InMemoryPublicLedgerEntryStore,
    )

    clock = _FixedClock(_datetime(2026, 1, 5, tzinfo=_UTC))
    actor = _ActorRef(actor_id=uuid4(), actor_type="service")
    ledger_store = InMemoryPublicLedgerEntryStore()
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = _AuditStore()

    defined = define_disclosure_policy(
        policy_store,
        audit_store,
        disclosure_policy_id=uuid4(),
        applies_to_subject_type="result_publication",
        field_rules=(
            FieldRule(
                field_path="yes_votes",
                disclosure_class=DisclosureClass.PUBLIC,
                transformation=Transformation.NONE,
            ),
            FieldRule(
                field_path="no_votes",
                disclosure_class=DisclosureClass.PUBLIC,
                transformation=Transformation.NONE,
            ),
        ),
        effective_from=clock.now(),
        version=1,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    activate_disclosure_policy(
        policy_store,
        audit_store,
        disclosure_policy_id=defined.policy.disclosure_policy_id,
        approved_by_role_id=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    tainted_raw_content = {
        "yes_votes": 120,
        "no_votes": 80,
        "vote_envelope_id": str(uuid4()),
        "encrypted_or_encoded_choice": "yes",
        "credential_proof": str(uuid4()),
    }
    result = publish_ledger_entry(
        ledger_store,
        policy_store,
        audit_store,
        public_ledger_entry_id=uuid4(),
        subject_type=LedgerSubjectType.RESULT_PUBLICATION,
        subject_id=uuid4(),
        subject_event_id=uuid4(),
        raw_content=tainted_raw_content,
        published_by_role_id=uuid4(),
        redaction_notice=None,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    assert "vote_envelope_id" not in result.entry.content_snapshot
    assert "encrypted_or_encoded_choice" not in result.entry.content_snapshot
    assert "credential_proof" not in result.entry.content_snapshot
    assert result.entry.content_snapshot.get("yes_votes") == 120

    payload_text = json.dumps(to_jsonable(result.event.payload))
    assert "vote_envelope_id" not in payload_text
    assert "encrypted_or_encoded_choice" not in payload_text
    assert "credential_proof" not in payload_text


def test_transparency_service_never_imports_delegation_or_voting_domain() -> None:
    """AST-based import-boundary check: no module in
    `epd2_transparency_service` ever imports `epd2_delegation_service` (a
    `DelegationSnapshot` is the closest thing this project has to a
    "delegation graph", and ADR-012 excludes it entirely) or
    `epd2_voting_service.domain` (the module that actually carries
    `VoteEnvelope`; PACK-04's one sanctioned voting-service import,
    `get_ballot`, lives in `epd2_voting_service.application` instead - see
    `tests/repository/test_service_boundaries.py`)."""
    import epd2_transparency_service

    package_dir = Path(inspect.getfile(epd2_transparency_service)).parent
    forbidden_modules = {"epd2_delegation_service"}
    for py_file in package_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name.split(".")[0] for alias in node.names}
                full_names = {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                names = {node.module.split(".")[0]} if node.module else set()
                full_names = {node.module} if node.module else set()
            else:
                continue
            leaked = names & forbidden_modules
            assert not leaked, f"{py_file} imports forbidden module(s): {leaked}"
            assert "epd2_voting_service.domain" not in full_names, (
                f"{py_file} imports epd2_voting_service.domain directly "
                f"(VoteEnvelope carrier) - only epd2_voting_service.application "
                f"is a sanctioned PACK-04 import"
            )


def test_voting_service_never_imports_account_or_identity_service() -> None:
    """AST-based import-boundary check (README.md /
    `tests/test_domain.py::test_no_code_path_resolves_a_vote_envelope_to_an_account`'s
    own precedent, checked here at the pack-cross-cutting CT-00 level
    too): no module in `epd2_voting_service` imports `epd2_account_service`
    or `epd2_identity_service` (ADR-008 - voting-service has no PACK-02
    dependency)."""
    import epd2_voting_service

    package_dir = Path(inspect.getfile(epd2_voting_service)).parent
    forbidden_modules = {"epd2_account_service", "epd2_identity_service"}
    for py_file in package_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                names = {node.module.split(".")[0]} if node.module else set()
            else:
                continue
            leaked = names & forbidden_modules
            assert not leaked, f"{py_file} imports forbidden module(s): {leaked}"
