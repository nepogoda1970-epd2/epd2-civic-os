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

from epd2_credential_service.domain import FORBIDDEN_FIELD_NAMES, ParticipationCredential


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
