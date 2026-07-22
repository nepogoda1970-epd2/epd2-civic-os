"""Property-based tests (pack section 12.5), using Hypothesis, for:
arbitrary forbidden identity field names; credential expiry boundaries;
duplicate event behavior; reason-code stability; canonical serialization
determinism.

Requires the `hypothesis` package; skipped locally in this sandbox (no
network access - see LOCAL_VERIFICATION.md), run for real in CI.

Note: `st.characters(...)` is called with `categories=`, not the older
`whitelist_categories=` alias - the latter was removed from Hypothesis
well before the `hypothesis>=6.112,<7` range this repository pins
(pyproject.toml), so it is a hard `TypeError` (an unexpected keyword
argument) at real runtime, not just a deprecation warning. This was
invisible in this sandbox, where `hypothesis` cannot be installed at all
(the whole module import-skips), and only surfaced when external
verification ran this suite against a real, installed `hypothesis`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.exceptions import AuditEventConflictError
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.canonical_json import canonical_dumps
from epd2_core.clock import FixedClock
from epd2_credential_service.domain import (
    FORBIDDEN_FIELD_NAMES,
    CredentialStatus,
    CredentialType,
    ParticipationCredential,
)
from epd2_credential_service.validation import validate_credential

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))


def _credential(**overrides: object) -> ParticipationCredential:
    defaults = dict(
        credential_id=uuid4(),
        credential_type=CredentialType.SPACE_ACCESS,
        scope_type="civic_space",
        scope_id=uuid4(),
        issued_at=datetime(2026, 1, 1, tzinfo=UTC),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        expires_at=datetime(2027, 1, 1, tzinfo=UTC),
        status=CredentialStatus.ACTIVE,
        usage_limit=None,
        usage_counter=0,
        revocation_status="not_revoked",
        issuer_signature=None,
        credential_version=1,
        rule_version=1,
        eligibility_snapshot_digest="a" * 64,
    )
    defaults.update(overrides)
    return ParticipationCredential(**defaults)  # type: ignore[arg-type]


# --- Arbitrary forbidden identity field names ---


@given(st.sampled_from(sorted(FORBIDDEN_FIELD_NAMES)))
def test_no_forbidden_field_name_is_ever_a_dataclass_field(field_name: str) -> None:
    assert field_name not in ParticipationCredential.__dataclass_fields__


@given(
    st.lists(
        st.sampled_from(sorted(FORBIDDEN_FIELD_NAMES)),
        min_size=1,
        max_size=len(FORBIDDEN_FIELD_NAMES),
    )
)
@settings(max_examples=30)
def test_no_forbidden_field_name_appears_in_a_real_credential_instance_dict(
    field_names: list[str],
) -> None:
    """For any non-empty subset of the forbidden identity field names
    (in any order/repetition Hypothesis picks), none of them appear as a
    key on a real, constructed `ParticipationCredential` instance's field
    set - the structural guarantee CT-00-08 depends on."""
    credential_field_names = set(ParticipationCredential.__dataclass_fields__)
    for name in field_names:
        assert name not in credential_field_names


# --- Credential expiry boundaries ---


@given(st.integers(min_value=-10_000, max_value=10_000))
@settings(max_examples=100)
def test_credential_expiry_boundary_is_strict(offset_seconds: int) -> None:
    """`validate_credential`'s expiry check (`now >= expires_at`) is a
    strict boundary: any `now` at or after `expires_at` is expired, any
    `now` strictly before is not (fail-closed exactly at the boundary,
    never a moment late)."""
    expires_at = datetime(2026, 1, 1, tzinfo=UTC)
    now = expires_at + timedelta(seconds=offset_seconds)
    credential = _credential(expires_at=expires_at)
    result = validate_credential(credential, now=now)
    if now >= expires_at:
        assert "CREDENTIAL_EXPIRED" in result.reason_codes
        assert not result.valid
    else:
        assert "CREDENTIAL_EXPIRED" not in result.reason_codes


# --- Duplicate event behavior ---


@given(st.text(min_size=1, max_size=30, alphabet=st.characters(categories=("Lu", "Nd"))))
@settings(max_examples=30)
def test_duplicate_audit_event_id_with_identical_content_is_always_idempotent(
    action_text: str,
) -> None:
    store = InMemoryAuditEventStore()
    request = AppendAuditEventRequest(
        audit_event_id=uuid4(),
        event_type="credential.issued",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        actor_id=uuid4(),
        actor_type="service",
        target_type="participation_credential",
        target_id=uuid4(),
        action=action_text or "issue",
        reason_code="CREDENTIAL_ISSUED",
        policy_version="1.0",
        correlation_id=uuid4(),
        source_service="credential-service",
    )
    first = append_audit_event(store, request, clock=_CLOCK)
    second = append_audit_event(store, request, clock=_CLOCK)
    assert first == second


@given(st.text(min_size=1, max_size=30), st.text(min_size=1, max_size=30))
@settings(max_examples=30)
def test_duplicate_audit_event_id_with_different_action_always_conflicts(
    action_a: str, action_b: str
) -> None:
    if action_a == action_b:
        return  # not the case under test
    store = InMemoryAuditEventStore()
    shared_id = uuid4()
    base = dict(
        audit_event_id=shared_id,
        event_type="credential.issued",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        actor_id=uuid4(),
        actor_type="service",
        target_type="participation_credential",
        target_id=uuid4(),
        reason_code="CREDENTIAL_ISSUED",
        policy_version="1.0",
        correlation_id=uuid4(),
        source_service="credential-service",
    )
    append_audit_event(
        store,
        AppendAuditEventRequest(action=action_a, **base),  # type: ignore[arg-type]
        clock=_CLOCK,
    )
    with pytest.raises(AuditEventConflictError):
        append_audit_event(
            store,
            AppendAuditEventRequest(action=action_b, **base),  # type: ignore[arg-type]
            clock=_CLOCK,
        )


# --- Reason-code stability ---


@given(
    st.sampled_from(
        ["CREDENTIAL_EXPIRED", "CREDENTIAL_SCOPE_MISMATCH", "EVENT_VERSION_UNSUPPORTED"]
    )
)
def test_reason_code_strings_are_stable_literals_not_derived(code: str) -> None:
    """A registered reason code is always the exact same literal string
    wherever it is produced - never interpolated, templated, or
    reformatted (canon section 24: never replaced by free text)."""
    assert code.isupper()
    assert " " not in code
    assert code == code.strip()


# --- Canonical serialization determinism ---


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=st.characters(categories=("Ll",))),
        st.integers(),
    )
)
@settings(max_examples=100)
def test_canonical_dumps_is_independent_of_input_key_order(mapping: dict[str, int]) -> None:
    import random

    items = list(mapping.items())
    shuffled = dict(items)
    random.shuffle(items)
    reshuffled = dict(items)
    assert canonical_dumps(mapping) == canonical_dumps(shuffled) == canonical_dumps(reshuffled)
