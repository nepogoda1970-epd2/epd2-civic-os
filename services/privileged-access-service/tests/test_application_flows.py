"""End-to-end governed flows through the command layer.

Each test here walks a whole lifecycle rather than one command, because
the guarantees that matter most - audit before event, evidence that
survives the session, an export that never carries a denied field - are
properties of a *sequence*, and a per-command test cannot see them.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from _privileged_builders import (
    FixedClock,
    StubAuthorizationPort,
    StubSourceAuthorizationPort,
    authority,
    build_stores,
)

from epd2_privileged_access_service import application as app
from epd2_privileged_access_service import storage as st
from epd2_privileged_access_service.access import GrantState, ResourceScope
from epd2_privileged_access_service.breakglass import BreakGlassState, EmergencyCondition
from epd2_privileged_access_service.classification import (
    EnforcementTier,
    SourceClassification,
    resolve_classification,
)
from epd2_privileged_access_service.disclosure import (
    CohortObservation,
    CohortPolicy,
    DisclosureRuleFamily,
)
from epd2_privileged_access_service.dlp import DlpControl, default_dlp_profile
from epd2_privileged_access_service.domain import (
    EffectiveWindow,
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
    ReasonCoded,
    RequestContext,
    RiskClass,
)
from epd2_privileged_access_service.exceptions import (
    BreakGlassNotificationUndeliveredError,
    OptimisticConcurrencyConflictError,
    SearchBallotContentProhibitedError,
)
from epd2_privileged_access_service.export import (
    DatasetItemReference,
    DatasetManifest,
    ExportRequest,
    ExportScope,
    ExportState,
    Recipient,
    RecipientCategory,
    RecipientObligation,
    TransferChannel,
)
from epd2_privileged_access_service.policy import REFERENCE_POLICY
from epd2_privileged_access_service.roles import OperationalAssignmentRole
from epd2_privileged_access_service.search import (
    IndexedRecord,
    IndexFieldPolicy,
    IndexPolicy,
    QueryRequest,
    SearchMode,
    SearchScope,
)
from epd2_privileged_access_service.sessions import SessionState, verify_session_chain
from epd2_privileged_access_service.storage import PrivilegedStores

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
SCOPE = OrganizationalScopeRef(organization_id=uuid4())
INTERNAL = resolve_classification(SourceClassification.INTERNAL)


def _reason(code: str) -> ReasonCoded:
    return ReasonCoded(reason_code=code, authority_reference="authority:1")


def _ctx(role: str, actor: str, scope: OrganizationalScopeRef = SCOPE) -> RequestContext:
    return RequestContext(
        scope=scope,
        authorities=(authority(role, scope, actor),),
        event_id=uuid4(),
    )


@pytest.fixture
def frame() -> tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]:
    return build_stores(), StubAuthorizationPort(), FixedClock(T0)


class TestPrivilegedAccessLifecycle:
    def test_request_approve_activate_session_seal(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        request_id, grant_id, session_id = uuid4(), uuid4(), uuid4()

        app.request_privileged_access(
            stores,
            context=_ctx("domain_administrator", "actor:subject"),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            request_id=request_id,
            subject_reference="actor:subject",
            requested_role=OperationalAssignmentRole.DOMAIN_ADMINISTRATOR,
            resource_scope=ResourceScope(domain="membership"),
            requested_operations=frozenset({"read_record"}),
            purpose=PurposeBinding(purpose=Purpose.OPERATIONS, justification_reference="j"),
            requested_window=EffectiveWindow(valid_from=T0, valid_until=T0 + timedelta(hours=4)),
            risk_class=RiskClass.MODERATE,
            data_classes=frozenset({"membership_record"}),
        )
        app.approve_privileged_access(
            stores,
            context=_ctx("security_administrator", "actor:security"),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            request_id=request_id,
            grant_id=grant_id,
            approvers=("actor:security",),
            reason=_reason("PRIVILEGE_ACCESS_APPROVAL_RECORDED"),
        )
        app.activate_privileged_access(
            stores,
            context=_ctx("domain_administrator", "actor:subject"),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            grant_id=grant_id,
            requested_operation="read_record",
            requested_domain="membership",
            requested_purpose=Purpose.OPERATIONS,
            reason=_reason("PRIVILEGE_ACCESS_ACTIVATION_RECORDED"),
        )
        app.start_privileged_session(
            stores,
            context=_ctx("domain_administrator", "actor:subject"),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            session_id=session_id,
            grant_id=grant_id,
            target_system="membership-service",
            target_domain="membership",
            requested_purpose=Purpose.OPERATIONS,
            reason=_reason("PRIVILEGE_SESSION_START_RECORDED"),
        )
        clock.advance(timedelta(minutes=5))
        app.record_session_operation(
            stores,
            context=_ctx("domain_administrator", "actor:subject"),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            session_id=session_id,
            sequence=1,
            operation="read_record",
            resource_domain="membership",
            resource_reference="rec:1",
            outcome="succeeded",
            summary_reference="summary:1",
        )
        clock.advance(timedelta(minutes=5))
        app.end_privileged_session(
            stores,
            context=_ctx("domain_administrator", "actor:subject"),
            port=port,
            clock=clock,
            session_id=session_id,
        )
        sealed = app.seal_privileged_session(
            stores,
            context=_ctx("audit_custodian", "actor:custodian"),
            port=port,
            clock=clock,
            session_id=session_id,
            evidence_bundle_reference="evidence-bundle:1",
        ).sealed

        assert sealed.verify()
        ok, broken = verify_session_chain(stores.sealed_sessions.list_chain())
        assert ok and broken is None
        session = stores.sessions.get(session_id)
        assert session is not None
        assert session.state is SessionState.SEALED
        grant = stores.grants.get(grant_id)
        assert grant is not None
        assert grant.state is GrantState.ACTIVE

    def test_an_operation_sequence_out_of_order_is_refused(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        """Idempotency by sequence: a retried call cannot inflate the
        session record."""
        stores, port, clock = frame
        request_id, grant_id, session_id = uuid4(), uuid4(), uuid4()
        _bootstrap_session(stores, port, clock, request_id, grant_id, session_id)
        app.record_session_operation(
            stores,
            context=_ctx("domain_administrator", "actor:subject"),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            session_id=session_id,
            sequence=1,
            operation="read_record",
            resource_domain="membership",
            resource_reference="rec:1",
            outcome="succeeded",
            summary_reference="summary:1",
        )
        with pytest.raises(OptimisticConcurrencyConflictError):
            app.record_session_operation(
                stores,
                context=_ctx("domain_administrator", "actor:subject"),
                port=port,
                clock=clock,
                policy=REFERENCE_POLICY,
                session_id=session_id,
                sequence=1,
                operation="read_record",
                resource_domain="membership",
                resource_reference="rec:1",
                outcome="succeeded",
                summary_reference="summary:1",
            )


def _bootstrap_session(
    stores: PrivilegedStores,
    port: StubAuthorizationPort,
    clock: FixedClock,
    request_id: UUID,
    grant_id: UUID,
    session_id: UUID,
) -> None:
    app.request_privileged_access(
        stores,
        context=_ctx("domain_administrator", "actor:subject"),
        port=port,
        clock=clock,
        policy=REFERENCE_POLICY,
        request_id=request_id,
        subject_reference="actor:subject",
        requested_role=OperationalAssignmentRole.DOMAIN_ADMINISTRATOR,
        resource_scope=ResourceScope(domain="membership"),
        requested_operations=frozenset({"read_record"}),
        purpose=PurposeBinding(purpose=Purpose.OPERATIONS, justification_reference="j"),
        requested_window=EffectiveWindow(valid_from=T0, valid_until=T0 + timedelta(hours=4)),
        risk_class=RiskClass.MODERATE,
        data_classes=frozenset({"membership_record"}),
    )
    app.approve_privileged_access(
        stores,
        context=_ctx("security_administrator", "actor:security"),
        port=port,
        clock=clock,
        policy=REFERENCE_POLICY,
        request_id=request_id,
        grant_id=grant_id,
        approvers=("actor:security",),
        reason=_reason("PRIVILEGE_ACCESS_APPROVAL_RECORDED"),
    )
    app.activate_privileged_access(
        stores,
        context=_ctx("domain_administrator", "actor:subject"),
        port=port,
        clock=clock,
        policy=REFERENCE_POLICY,
        grant_id=grant_id,
        requested_operation="read_record",
        requested_domain="membership",
        requested_purpose=Purpose.OPERATIONS,
        reason=_reason("PRIVILEGE_ACCESS_ACTIVATION_RECORDED"),
    )
    app.start_privileged_session(
        stores,
        context=_ctx("domain_administrator", "actor:subject"),
        port=port,
        clock=clock,
        policy=REFERENCE_POLICY,
        session_id=session_id,
        grant_id=grant_id,
        target_system="membership-service",
        target_domain="membership",
        requested_purpose=Purpose.OPERATIONS,
        reason=_reason("PRIVILEGE_SESSION_START_RECORDED"),
    )


class TestBreakGlassFlow:
    def _request_and_approve(
        self,
        stores: PrivilegedStores,
        port: StubAuthorizationPort,
        clock: FixedClock,
        activation_id: UUID,
    ) -> None:
        app.request_break_glass(
            stores,
            context=_ctx("system_administrator", "actor:oncall"),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            activation_id=activation_id,
            condition=EmergencyCondition(
                condition_reference="incident:INC-1",
                condition_class="service_outage",
                declared_at=T0,
                declared_by="actor:oncall",
            ),
            purpose=PurposeBinding(purpose=Purpose.INCIDENT_RESPONSE, justification_reference="j"),
            resource_domain="membership",
            permitted_operations=frozenset({"read_record"}),
            window=EffectiveWindow(valid_from=T0, valid_until=T0 + timedelta(hours=1)),
            approver_reference="actor:bgapprover",
            reason=_reason("PRIVILEGE_BREAK_GLASS_REQUEST_RECORDED"),
        )
        app.approve_break_glass(
            stores,
            context=_ctx("break_glass_approver", "actor:bgapprover"),
            port=port,
            clock=clock,
            activation_id=activation_id,
            reason=_reason("PRIVILEGE_BREAK_GLASS_APPROVAL_RECORDED"),
        )

    def test_a_delivered_notification_activates(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        activation_id = uuid4()
        self._request_and_approve(stores, port, clock, activation_id)
        result = app.activate_break_glass(
            stores,
            context=_ctx("system_administrator", "actor:oncall"),
            port=port,
            clock=clock,
            activation_id=activation_id,
            recipient_class="security_oversight",
            reason=_reason("PRIVILEGE_BREAK_GLASS_ACTIVATION_RECORDED"),
        )
        assert result.activation.state is BreakGlassState.ACTIVATED
        types = [e.event_type for e in stores.sink.published()]
        assert "break_glass.notification_dispatched" in types

    def test_an_undelivered_notification_escalates_and_refuses(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        """`P12-BG-008`: emergency access whose notification failed is
        emergency access nobody was told about. The failure is recorded
        and escalated, and the activation still refuses."""
        _, port, clock = frame
        stores = build_stores(notifications=st.ReferenceNotificationAdapter(deliver=False))
        activation_id = uuid4()
        self._request_and_approve(stores, port, clock, activation_id)
        with pytest.raises(BreakGlassNotificationUndeliveredError):
            app.activate_break_glass(
                stores,
                context=_ctx("system_administrator", "actor:oncall"),
                port=port,
                clock=clock,
                activation_id=activation_id,
                recipient_class="security_oversight",
                reason=_reason("PRIVILEGE_BREAK_GLASS_ACTIVATION_RECORDED"),
            )
        activation = stores.break_glass.get(activation_id)
        assert activation is not None
        assert activation.state is BreakGlassState.ESCALATED
        types = [e.event_type for e in stores.sink.published()]
        assert "break_glass.notification_dispatched" in types


class TestSearchFlow:
    def _index(
        self, stores: PrivilegedStores, port: StubAuthorizationPort, clock: FixedClock
    ) -> None:
        policy = IndexPolicy(
            index_name="main",
            policy_version="pack-12-index/v1",
            mode=SearchMode.SCOPED_DOMAIN,
            field_policies=(
                IndexFieldPolicy(
                    record_class="membership_record",
                    indexable_fields=frozenset({"title"}),
                    snippet_fields=frozenset({"title"}),
                ),
            ),
            admitted_tiers=frozenset({EnforcementTier.T1_INTERNAL}),
        )
        app.change_index_policy(
            stores,
            context=_ctx("security_administrator", "actor:security"),
            port=port,
            clock=clock,
            policy=policy,
        )
        stores.index.index(
            IndexedRecord(
                record_reference="rec:1",
                domain="membership",
                record_class="membership_record",
                organization_scope=SCOPE,
                classification=INTERNAL,
                fields={"title": "Board minutes"},
                indexed_at=T0,
            )
        )

    def test_a_query_emits_submission_authorization_and_execution(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        self._index(stores, port, clock)
        result = app.submit_search_query(
            stores,
            context=_ctx("domain_administrator", "actor:subject"),
            port=port,
            source_port=StubSourceAuthorizationPort(),
            clock=clock,
            request=QueryRequest(
                query_id=uuid4(),
                requester_reference="actor:subject",
                mode=SearchMode.SCOPED_DOMAIN,
                scope=SearchScope(organization_scope=SCOPE, domains=frozenset({"membership"})),
                purpose=Purpose.OPERATIONS,
                query_digest="d" * 64,
                submitted_at=T0,
            ),
            index_name="main",
        )
        types = [e.event_type for e in stores.sink.published()]
        assert "search_query.submitted" in types
        assert "search_query.authorized" in types
        assert "search_query.executed" in types
        assert result.decision.authorized_count == 1
        assert stores.query_audit.list_for_scope(scope=SCOPE)

    def test_a_refused_query_is_recorded_as_denied_and_still_raises(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        """A structural refusal still leaves a governed trace. The
        command records the submission and the denial, then re-raises -
        it does not swallow the refusal to keep the audit tidy."""
        stores, port, clock = frame
        self._index(stores, port, clock)
        with pytest.raises(SearchBallotContentProhibitedError):
            app.submit_search_query(
                stores,
                context=_ctx("domain_administrator", "actor:subject"),
                port=port,
                source_port=StubSourceAuthorizationPort(),
                clock=clock,
                request=QueryRequest(
                    query_id=uuid4(),
                    requester_reference="actor:subject",
                    mode=SearchMode.SCOPED_DOMAIN,
                    scope=SearchScope(
                        organization_scope=SCOPE, domains=frozenset({"ballot_content"})
                    ),
                    purpose=Purpose.OPERATIONS,
                    query_digest="d" * 64,
                    submitted_at=T0,
                ),
                index_name="main",
            )
        types = [e.event_type for e in stores.sink.published()]
        assert "search_query.denied" in types

    def test_a_suppressed_result_emits_its_own_event(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        self._index(stores, port, clock)
        app.submit_search_query(
            stores,
            context=_ctx("domain_administrator", "actor:subject"),
            port=port,
            source_port=StubSourceAuthorizationPort(openable=frozenset()),
            clock=clock,
            request=QueryRequest(
                query_id=uuid4(),
                requester_reference="actor:subject",
                mode=SearchMode.SCOPED_DOMAIN,
                scope=SearchScope(organization_scope=SCOPE, domains=frozenset({"membership"})),
                purpose=Purpose.OPERATIONS,
                query_digest="d" * 64,
                submitted_at=T0,
            ),
            index_name="main",
        )
        types = [e.event_type for e in stores.sink.published()]
        assert "search_query.restricted_result_suppressed" in types


class TestExportFlow:
    def test_request_assess_approve_generate_deliver_access_revoke_attest(
        self, frame: tuple[PrivilegedStores, StubAuthorizationPort, FixedClock]
    ) -> None:
        stores, port, clock = frame
        export_id, assessment_id, artifact_id = uuid4(), uuid4(), uuid4()

        request = ExportRequest(
            export_id=export_id,
            requester_reference="actor:requester",
            purpose=PurposeBinding(
                purpose=Purpose.DATA_SUBJECT_REQUEST,
                justification_reference="j",
                basis_reference="basis:1",
            ),
            scope=ExportScope(
                domains=frozenset({"membership"}),
                record_classes=frozenset({"membership_record"}),
                organization_scope=SCOPE,
            ),
            requested_fields=frozenset({"title"}),
            requested_format="csv",
            recipient=Recipient(
                recipient_reference="recipient:1",
                category=RecipientCategory.INTERNAL_SAME_SCOPE,
                organization_scope=SCOPE,
                obligation=RecipientObligation(
                    retention_limit=timedelta(days=30),
                    resharing_permitted=False,
                    destruction_required=True,
                    obligation_reference="obligation:1",
                ),
            ),
            transfer_channel=TransferChannel.PLATFORM_DOWNLOAD,
            requested_at=T0,
            data_owner_reference="actor:owner",
        )
        app.request_data_export(
            stores,
            context=_ctx("data_owner", "actor:owner"),
            port=port,
            clock=clock,
            request=request,
            classifications=[INTERNAL],
            has_search_permission=True,
            has_read_permission=True,
            has_admin_privilege=True,
            has_data_owner_authority=True,
            has_approver=True,
        )
        app.record_dlp_assessment(
            stores,
            context=_ctx("dlp_security_officer", "actor:dlp"),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            export_id=export_id,
            assessment_id=assessment_id,
            completed_controls=frozenset(DlpControl),
            required_transforms=frozenset(),
            outcome="passed",
            record_count=1,
        )
        # Attach a disclosure assessment reference so approval can proceed.
        disclosure_id = app.assess_disclosure_risk(
            stores,
            context=_ctx("disclosure_control_reviewer", "actor:disclosure"),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            assessment_id=uuid4(),
            release_class="membership_statistics",
            cohort_policy=CohortPolicy(
                policy_id=uuid4(),
                release_class="membership_statistics",
                minimum_cohort_size=REFERENCE_POLICY.cohort_threshold,
                active_rule_families=frozenset(DisclosureRuleFamily),
            ),
            cohorts=[
                CohortObservation(
                    cohort_key="region:north", size=50, dimensions=frozenset({"region"})
                )
            ],
            total_population=100,
            suppression=None,
            release_history_reference="history:1",
            requester_reference="actor:requester",
        ).assessment.assessment_id
        app.record_disclosure_assessment(
            stores,
            context=_ctx("disclosure_control_reviewer", "actor:disclosure"),
            port=port,
            clock=clock,
            export_id=export_id,
            assessment_id=disclosure_id,
        )
        app.approve_data_export(
            stores,
            context=_ctx("export_approver", "actor:exportapprover"),
            port=port,
            clock=clock,
            export_id=export_id,
            permitted_fields=frozenset({"title"}),
            reason=_reason("EXPORT_APPROVAL_RECORDED"),
        )
        manifest = DatasetManifest(
            manifest_id=uuid4(),
            export_id=export_id,
            items=(
                DatasetItemReference(
                    record_reference="rec:1",
                    domain="membership",
                    classification=INTERNAL,
                    content_digest="a" * 64,
                ),
            ),
            permitted_fields=frozenset({"title"}),
            policy_version=REFERENCE_POLICY.policy_version,
            classification_mapping_version=INTERNAL.mapping_version,
            generated_at=T0,
        )
        artifact = app.generate_export_artifact(
            stores,
            context=_ctx("data_owner", "actor:owner"),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            export_id=export_id,
            artifact_id=artifact_id,
            manifest=manifest,
            rows=[{"title": "Board minutes", "home_address": "somewhere"}],
            dlp_profile=default_dlp_profile("membership_record", uuid4()),
            class_fields=frozenset({"title"}),
            purpose_fields=frozenset({"title"}),
        ).artifact

        assert artifact.projection == ({"title": "Board minutes"},)
        assert artifact.is_authoritative is False

        app.deliver_export_artifact(
            stores,
            context=_ctx("data_owner", "actor:owner"),
            port=port,
            clock=clock,
            artifact_id=artifact_id,
            reason=_reason("EXPORT_ARTIFACT_DELIVERY_RECORDED"),
        )
        accessed = app.access_export_artifact(
            stores,
            context=_ctx("data_owner", "actor:owner"),
            port=port,
            clock=clock,
            policy=REFERENCE_POLICY,
            artifact_id=artifact_id,
            access_id=uuid4(),
        ).artifact
        assert accessed.access_count == 1

        app.revoke_data_export(
            stores,
            context=_ctx("data_owner", "actor:owner"),
            port=port,
            clock=clock,
            export_id=export_id,
            artifact_id=artifact_id,
            reason=_reason("EXPORT_REVOCATION_RECORDED"),
        )
        revoked = stores.artifacts.get(artifact_id)
        assert revoked is not None
        assert revoked.revoked

        app.attest_export_destruction(
            stores,
            context=_ctx("data_owner", "actor:owner"),
            port=port,
            clock=clock,
            export_id=export_id,
            attestation_id=uuid4(),
            attesting_party="recipient:1",
            attestation_reference="attestation:1",
        )
        final = stores.exports.get(export_id)
        assert final is not None
        assert final.state is ExportState.DESTRUCTION_ATTESTED

        types = [e.event_type for e in stores.sink.published()]
        for expected in (
            "data_export.requested",
            "data_export.dlp_assessment_completed",
            "data_export.disclosure_assessment_completed",
            "data_export.approved",
            "export_artifact.generated",
            "export_artifact.delivered",
            "export_artifact.accessed",
            "data_export.revoked",
            "data_export.destruction_attested",
        ):
            assert expected in types, expected
        assert len(stores.audit.list_all()) >= len(types)
