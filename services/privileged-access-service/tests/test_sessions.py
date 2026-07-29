"""Privileged session evidence (`P12-SES-*`, FIR-INV-010, ADR-063)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
)
from epd2_privileged_access_service.exceptions import (
    AssignmentNotEffectiveDatedError,
    ForbiddenTransitionError,
    PrivilegedSessionSecretForbiddenError,
    SessionEvidenceIncompleteError,
)
from epd2_privileged_access_service.sessions import (
    GENESIS_PREVIOUS_HASH,
    OperationSummary,
    PrivilegedSession,
    SealedPrivilegedSession,
    SessionState,
    compute_session_hash,
    verify_session_chain,
)

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
SCOPE = OrganizationalScopeRef(organization_id=uuid4())


def _session(**overrides: object) -> PrivilegedSession:
    base: dict[str, object] = {
        "session_id": uuid4(),
        "actor_reference": "actor:subject",
        "effective_role": "domain_administrator",
        "grant_reference": uuid4(),
        "purpose": PurposeBinding(purpose=Purpose.OPERATIONS, justification_reference="j"),
        "target_system": "membership-service",
        "target_domain": "membership",
        "organization_scope": SCOPE,
        "permitted_operations": frozenset({"read_record"}),
        "started_at": T0,
    }
    base.update(overrides)
    return PrivilegedSession(**base)  # type: ignore[arg-type]


def _summary(sequence: int = 1) -> OperationSummary:
    return OperationSummary(
        sequence=sequence,
        occurred_at=T0 + timedelta(minutes=sequence),
        operation="read_record",
        resource_domain="membership",
        resource_reference=f"rec:{sequence}",
        outcome="succeeded",
        summary_reference=f"summary:{sequence}",
    )


def _sealed(session: PrivilegedSession | None = None) -> SealedPrivilegedSession:
    live = (session or _session()).with_operation(_summary())
    return live.end(T0 + timedelta(minutes=10)).seal(evidence_bundle_reference="evidence-bundle:1")


class TestSessionRecord:
    def test_operations_accumulate_only_while_started(self) -> None:
        ended = _session().end(T0 + timedelta(minutes=1))
        with pytest.raises(ForbiddenTransitionError):
            ended.with_operation(_summary())

    def test_an_end_before_the_start_is_refused(self) -> None:
        with pytest.raises(SessionEvidenceIncompleteError):
            _session().end(T0 - timedelta(minutes=1))

    def test_accessed_resources_are_deduplicated(self) -> None:
        session = _session().with_accessed_resource("rec:1").with_accessed_resource("rec:1")
        assert session.accessed_resources == ("rec:1",)

    def test_search_and_export_actions_are_linked_not_copied(self) -> None:
        query_id, export_id = uuid4(), uuid4()
        session = _session().with_search_action(query_id).with_export_action(export_id)
        assert session.search_actions == (query_id,)
        assert session.export_actions == (export_id,)

    def test_hashable_fields_cover_every_field(self) -> None:
        """A snapshot that is only nearly complete leaves the omitted
        fields outside the tamper-evidence hash and signals nothing about
        the gap."""
        session = _session()
        hashed = set(session.hashable_fields())
        declared = set(PrivilegedSession.__dataclass_fields__) - {
            "state",
            "previous_hash",
        }
        assert declared <= hashed


class TestSealing:
    def test_only_an_ended_session_can_be_sealed(self) -> None:
        with pytest.raises(ForbiddenTransitionError):
            _session().seal(evidence_bundle_reference="evidence-bundle:1")

    def test_the_sealed_type_has_no_mutator(self) -> None:
        """`P12-SES-004`: after sealing, the only operations are reading
        and verifying. A distinct type, not a flag on the same one."""
        forbidden = {"with_operation", "end", "seal", "with_accessed_resource"}
        assert not (forbidden & set(dir(SealedPrivilegedSession)))

    def test_a_sealed_session_verifies_against_its_own_payload(self) -> None:
        sealed = _sealed()
        assert sealed.verify()

    def test_altering_the_payload_breaks_verification(self) -> None:
        """Tamper *evidence*: the alteration is detectable. Nothing here
        prevented it, and nothing claims to."""
        sealed = _sealed()
        tampered = replace(
            sealed, sealed_payload={**sealed.sealed_payload, "actor_reference": "actor:x"}
        )
        assert not tampered.verify()

    def test_the_evidence_bundle_reference_is_mandatory(self) -> None:
        live = _session().end(T0 + timedelta(minutes=1))
        with pytest.raises(AssignmentNotEffectiveDatedError):
            live.seal(evidence_bundle_reference="   ")

    def test_the_record_carries_references_never_content(self) -> None:
        """`P12-SES-007`: a session records *that* an operation happened
        and points at a summary; it never carries the content the
        operation touched.

        Asserted structurally over the field names, because the guarantee
        is about the shape of the record. `OperationSummary` has a
        `summary_reference` and no `payload`, `body`, `content` or
        `response` field, so there is no field a future caller could put
        content into without changing the type."""
        content_fields = {"payload", "body", "content", "response", "value", "data"}
        assert not (content_fields & set(OperationSummary.__dataclass_fields__))
        assert not (content_fields & set(PrivilegedSession.__dataclass_fields__))

    def test_a_prohibited_key_is_refused_at_seal_time(self) -> None:
        """The guard that runs inside `seal`, exercised directly: a
        payload carrying a credential key never becomes sealed evidence,
        not even briefly."""
        payload = _session().hashable_fields()
        payload["private_key"] = "x"
        from epd2_privileged_access_service.domain import reject_prohibited_payload_keys

        with pytest.raises(PrivilegedSessionSecretForbiddenError):
            reject_prohibited_payload_keys(payload, context="test")


class TestChain:
    def test_a_first_seal_links_to_the_genesis_hash(self) -> None:
        assert _sealed().previous_hash == GENESIS_PREVIOUS_HASH

    def test_a_chain_of_seals_verifies(self) -> None:
        first = _sealed()
        second_session = replace(
            _session().with_operation(_summary(2)),
            previous_hash=first.integrity_reference,
        )
        second = second_session.end(T0 + timedelta(minutes=20)).seal(
            evidence_bundle_reference="evidence-bundle:2"
        )
        ok, broken_at = verify_session_chain((first, second))
        assert ok
        assert broken_at is None

    def test_a_broken_link_reports_its_index(self) -> None:
        first = _sealed()
        detached = (
            replace(_session().with_operation(_summary(2)), previous_hash="0" * 64)
            .end(T0 + timedelta(minutes=20))
            .seal(evidence_bundle_reference="bundle:2")
        )
        ok, broken_at = verify_session_chain((first, detached))
        assert not ok
        assert broken_at == 1

    def test_the_hash_rule_matches_the_repository_wide_one(self) -> None:
        """`sha256(canonical_dumps(payload) + previous_hash)` - the same
        rule PACK-02's audit chain and PACK-11's document versions use, so
        one verification procedure covers all three."""
        payload: dict[str, object] = {"b": 2, "a": 1}
        reordered: dict[str, object] = {"a": 1, "b": 2}
        assert compute_session_hash(payload, "0" * 64) == compute_session_hash(reordered, "0" * 64)


class TestStates:
    def test_the_state_set_is_closed(self) -> None:
        assert {s.value for s in SessionState} == {
            "started",
            "ended",
            "sealed",
            "reviewed",
        }
