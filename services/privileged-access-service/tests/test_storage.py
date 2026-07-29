"""Storage ports and reference adapters (`P12-STOR-*`, `OD-P12-06`)."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from _privileged_builders import build_stores

from epd2_privileged_access_service import storage
from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
)
from epd2_privileged_access_service.exceptions import (
    AuditMutationProhibitedError,
    SessionEvidenceIncompleteError,
)
from epd2_privileged_access_service.sessions import PrivilegedSession
from epd2_privileged_access_service.storage import (
    PrivilegedStores,
    QueryAudit,
    delete_privileged_record,
)

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
SCOPE = OrganizationalScopeRef(organization_id=uuid4())
OTHER = OrganizationalScopeRef(organization_id=uuid4())

_PORTS = [
    obj
    for name, obj in vars(storage).items()
    if inspect.isclass(obj) and name.endswith("Store") and not name.startswith("InMemory")
]
_ADAPTERS = [
    obj
    for name, obj in vars(storage).items()
    if inspect.isclass(obj) and name.startswith("InMemory")
]


class TestNoDeletion:
    @pytest.mark.parametrize("port", _PORTS, ids=lambda c: c.__name__)
    def test_no_storage_port_declares_a_delete_operation(self, port: type) -> None:
        """ "Revocation is not deletion" has to be structural. A port with
        a `delete` method is a port through which a governed record can
        leave the system, whatever the policy says."""
        forbidden = {"delete", "remove_record", "purge", "drop", "erase", "destroy"}
        assert not (forbidden & set(vars(port)))

    @pytest.mark.parametrize("adapter", _ADAPTERS, ids=lambda c: c.__name__)
    def test_no_in_memory_adapter_declares_one_either(self, adapter: type) -> None:
        forbidden = {"delete", "purge", "drop", "erase", "destroy"}
        assert not (forbidden & set(vars(adapter)))

    def test_the_deletion_helper_exists_only_to_refuse(self) -> None:
        """A function that raises is a control; "we simply never call it"
        is not."""
        with pytest.raises(AuditMutationProhibitedError):
            delete_privileged_record(object())


class TestSealedSessionChain:
    def _session(self, previous_hash: str) -> PrivilegedSession:
        return PrivilegedSession(
            session_id=uuid4(),
            actor_reference="actor:subject",
            effective_role="domain_administrator",
            grant_reference=uuid4(),
            purpose=PurposeBinding(purpose=Purpose.OPERATIONS, justification_reference="j"),
            target_system="membership-service",
            target_domain="membership",
            organization_scope=SCOPE,
            permitted_operations=frozenset({"read_record"}),
            started_at=T0,
            previous_hash=previous_hash,
        )

    def test_a_sealed_session_cannot_be_replaced(self) -> None:
        """`P12-SES-004`: append-only means the second append under the
        same id is refused, not silently ignored and not overwritten."""
        store = storage.InMemorySealedSessionStore()
        session = self._session(store.head_hash())
        sealed = session.end(T0 + timedelta(minutes=1)).seal(evidence_bundle_reference="bundle:1")
        store.append(sealed)
        with pytest.raises(SessionEvidenceIncompleteError):
            store.append(sealed)

    def test_the_head_hash_advances_with_each_append(self) -> None:
        store = storage.InMemorySealedSessionStore()
        genesis = store.head_hash()
        sealed = (
            self._session(genesis)
            .end(T0 + timedelta(minutes=1))
            .seal(evidence_bundle_reference="bundle:1")
        )
        store.append(sealed)
        assert store.head_hash() != genesis
        assert store.head_hash() == sealed.integrity_reference


class TestScopeIsolation:
    def test_a_query_audit_listing_never_crosses_an_organization(self) -> None:
        store = storage.InMemoryQueryAuditStore()
        for scope in (SCOPE, OTHER):
            store.save(
                QueryAudit(
                    query_id=uuid4(),
                    organization_scope=scope,
                    requester_reference="actor:a",
                    mode="scoped_domain",
                    purpose="operations",
                    query_digest="d" * 64,
                    authorized_count=1,
                    suppressed_band="none",
                    policy_version="v1",
                    executed_at=T0,
                )
            )
        assert len(store.list_for_scope(scope=SCOPE)) == 1
        assert len(store.list_for_scope(scope=OTHER)) == 1

    def test_similar_digests_are_scoped_and_requester_bound(self) -> None:
        store = storage.InMemoryQueryAuditStore()
        store.save(
            QueryAudit(
                query_id=uuid4(),
                organization_scope=SCOPE,
                requester_reference="actor:a",
                mode="scoped_domain",
                purpose="operations",
                query_digest="abcd" + "0" * 60,
                authorized_count=1,
                suppressed_band="none",
                policy_version="v1",
                executed_at=T0,
            )
        )
        assert store.similar_digests(
            scope=SCOPE, requester_reference="actor:a", digest_prefix="abcd"
        )
        assert not store.similar_digests(
            scope=OTHER, requester_reference="actor:a", digest_prefix="abcd"
        )
        assert not store.similar_digests(
            scope=SCOPE, requester_reference="actor:b", digest_prefix="abcd"
        )


class TestBundle:
    def test_the_bundle_names_every_store_the_command_layer_needs(self) -> None:
        bundle = build_stores()
        assert isinstance(bundle, PrivilegedStores)
        assert len(PrivilegedStores.__dataclass_fields__) == 22

    def test_two_bundles_share_no_state(self) -> None:
        """A shared bundle would let one caller's idempotency record
        silently satisfy another's replay check."""
        first, second = build_stores(), build_stores()
        assert first.idempotency is not second.idempotency
        assert first.audit is not second.audit


class TestNotificationAdapter:
    def test_a_failing_adapter_reports_the_failure_rather_than_hiding_it(self) -> None:
        adapter = storage.ReferenceNotificationAdapter(deliver=False)
        outcome = adapter.dispatch(
            activation_id=uuid4(),
            organization_scope=SCOPE,
            recipient_class="security_oversight",
            activator_reference="actor:a",
        )
        assert not outcome.delivered
        assert outcome.failure_reason

    def test_a_suppressing_adapter_records_who_suppressed(self) -> None:
        adapter = storage.ReferenceNotificationAdapter(suppressed_by="actor:a")
        outcome = adapter.dispatch(
            activation_id=uuid4(),
            organization_scope=SCOPE,
            recipient_class="security_oversight",
            activator_reference="actor:a",
        )
        assert outcome.suppressed_by == "actor:a"
