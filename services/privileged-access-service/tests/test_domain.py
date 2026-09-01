"""Domain value objects: what cannot be constructed (`P12-PAM-002`,
`P12-PAM-003`, `P12-SES-007`)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_privileged_access_service.domain import (
    DUAL_CONTROL_RISK_CLASSES,
    PROHIBITED_PAYLOAD_KEYS,
    AuthorityReference,
    EffectiveWindow,
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
    ReasonCoded,
    RequestContext,
    RiskClass,
    deterministic_digest,
    reject_prohibited_payload_keys,
    require_timezone,
)
from epd2_privileged_access_service.exceptions import (
    AssignmentNotEffectiveDatedError,
    JustificationMissingError,
    OrganizationScopeMismatchError,
    OrganizationScopeUndeterminedError,
    PrivilegedSessionSecretForbiddenError,
    PrivilegePurposeMismatchError,
    StandingAccessProhibitedError,
)

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)


class TestEffectiveWindow:
    def test_has_no_unbounded_option(self) -> None:
        """`P12-PAM-003`: a standing grant is not expressible.

        The absence of a `valid_until=None` case is the control. A test
        that only checked a policy ceiling would pass against a model
        that still permitted "forever" when the policy was misread."""
        fields = {f for f in EffectiveWindow.__dataclass_fields__}
        assert fields == {"valid_from", "valid_until"}

    def test_refuses_non_positive_duration(self) -> None:
        with pytest.raises(StandingAccessProhibitedError):
            EffectiveWindow(valid_from=T0, valid_until=T0)

    def test_refuses_naive_datetimes(self) -> None:
        naive = datetime(2026, 3, 1, 9, 0)
        with pytest.raises(AssignmentNotEffectiveDatedError):
            EffectiveWindow(valid_from=naive, valid_until=T0 + timedelta(hours=1))

    def test_covers_is_half_open(self) -> None:
        window = EffectiveWindow(valid_from=T0, valid_until=T0 + timedelta(hours=1))
        assert window.covers(T0)
        assert not window.covers(T0 + timedelta(hours=1))


class TestOrganizationalScope:
    def test_undetermined_scope_denies_rather_than_defaults(self) -> None:
        """`P12-ORG-004`: `None` is not "any scope"."""
        scope = OrganizationalScopeRef(organization_id=uuid4())
        with pytest.raises(OrganizationScopeUndeterminedError):
            scope.assert_matches(None)

    def test_foreign_scope_is_a_distinct_refusal(self) -> None:
        a = OrganizationalScopeRef(organization_id=uuid4())
        b = OrganizationalScopeRef(organization_id=uuid4())
        with pytest.raises(OrganizationScopeMismatchError):
            a.assert_matches(b)


class TestPurposeBinding:
    def test_requires_a_justification(self) -> None:
        with pytest.raises(JustificationMissingError):
            PurposeBinding(purpose=Purpose.OPERATIONS, justification_reference="   ")

    def test_purpose_may_not_widen(self) -> None:
        binding = PurposeBinding(purpose=Purpose.AUDIT, justification_reference="j")
        binding.assert_admits(Purpose.AUDIT)
        with pytest.raises(PrivilegePurposeMismatchError):
            binding.assert_admits(Purpose.OPERATIONS)

    def test_investigation_is_a_purpose_not_a_mode(self) -> None:
        """`OD-P12-02`'s resolution, asserted structurally."""
        assert Purpose.INVESTIGATION in set(Purpose)


class TestProhibitedPayloadKeys:
    @pytest.mark.parametrize(
        "key",
        ["password", "api_key", "private_key", "ballot_content", "session_token"],
    )
    def test_named_key_is_refused_at_any_depth(self, key: str) -> None:
        with pytest.raises(PrivilegedSessionSecretForbiddenError):
            reject_prohibited_payload_keys({"outer": {"inner": {key: "x"}}}, context="t")

    def test_refuses_inside_a_list(self) -> None:
        with pytest.raises(PrivilegedSessionSecretForbiddenError):
            reject_prohibited_payload_keys({"rows": [{"ok": 1}, {"password": "x"}]}, context="t")

    def test_permits_an_ordinary_payload(self) -> None:
        reject_prohibited_payload_keys({"grant_id": "abc", "state": "active"}, context="t")

    def test_the_registry_is_not_empty(self) -> None:
        assert len(PROHIBITED_PAYLOAD_KEYS) >= 10


class TestAuthorityReference:
    def test_wire_form_drops_the_actor_reference(self) -> None:
        """Canon 20 permits a reference to the acting authority, never the
        identity behind it."""
        scope = OrganizationalScopeRef(organization_id=uuid4())
        ref = AuthorityReference(
            authority_id=uuid4(),
            role_code="security_administrator",
            scope=scope,
            actor_reference="actor:alice",
        )
        assert "actor_reference" not in ref.to_payload()
        assert ref.to_state_payload()["actor_reference"] == "actor:alice"


class TestReasonCoded:
    def test_refuses_a_lower_case_code(self) -> None:
        """`P12-RSN-002`: a registered code is upper-case by convention
        across every pack, so a lower-case string is a free-text reason
        wearing a code's clothes."""
        with pytest.raises(AssignmentNotEffectiveDatedError):
            ReasonCoded(reason_code="permission_denied", authority_reference="a")

    def test_refuses_a_blank_code(self) -> None:
        with pytest.raises(AssignmentNotEffectiveDatedError):
            ReasonCoded(reason_code="  ", authority_reference="a")

    def test_requires_the_invoking_authority(self) -> None:
        """A reason with no authority behind it records who was blamed,
        not who decided."""
        with pytest.raises(AssignmentNotEffectiveDatedError):
            ReasonCoded(reason_code="PERMISSION_DENIED", authority_reference="")


class TestRequestContext:
    def test_require_scope_fails_closed(self) -> None:
        with pytest.raises(OrganizationScopeUndeterminedError):
            RequestContext(scope=None).require_scope()


class TestRiskClass:
    def test_dual_control_covers_high_and_critical(self) -> None:
        assert frozenset({RiskClass.HIGH, RiskClass.CRITICAL}) == DUAL_CONTROL_RISK_CLASSES


class TestHelpers:
    def test_digest_is_deterministic_and_order_sensitive(self) -> None:
        assert deterministic_digest("a", "b") == deterministic_digest("a", "b")
        assert deterministic_digest("a", "b") != deterministic_digest("b", "a")

    def test_require_timezone_rejects_naive(self) -> None:
        with pytest.raises(AssignmentNotEffectiveDatedError):
            require_timezone(datetime(2026, 1, 1), context="t")
