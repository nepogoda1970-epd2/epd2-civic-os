"""Tests for epd2_tally_service.application: `start_tally`, `complete_tally`,
`verify_tally`, `publish_result` - permission checks, transitions, event
emission (including the no-event failure path for a failed verification),
audit-event creation, and CT-00-04 idempotency (both storage- and
event_id-level).

Also includes a structural, AST-based regression proving this package
never imports `epd2_voting_service` anywhere (ADR-008 item 3: no
PACK-03<->PACK-03 import) - the same style of check
`epd2_voting_service`'s own `tests/test_domain.py` uses to prove it never
imports `epd2_account_service`/`epd2_identity_service`.
"""

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_tally_service.application import (
    PermissionDeniedError,
    PublishResultResult,
    complete_tally,
    publish_result,
    start_tally,
    verify_tally,
)
from epd2_tally_service.domain import QuorumResult, TallyVerificationStatus, ThresholdResult
from epd2_tally_service.exceptions import ForbiddenTallyTransitionError, UnknownTallyError
from epd2_tally_service.storage import InMemoryResultPublicationStore, InMemoryTallyStore

_NOW = datetime(2026, 1, 5, tzinfo=UTC)
_CLOCK = FixedClock(_NOW)


def _actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="service")


class _Fixture:
    def __init__(self) -> None:
        self.tally_store = InMemoryTallyStore()
        self.result_store = InMemoryResultPublicationStore()
        self.audit_store = InMemoryAuditEventStore()


def _start(fx: _Fixture, **overrides: object) -> UUID:
    tally_id = uuid4()
    kwargs: dict[str, object] = {
        "tally_id": tally_id,
        "ballot_id": uuid4(),
        "input_set_hash": "a" * 64,
        "algorithm_version": "1.0",
        "actor": _actor(),
        "actor_is_authorized": True,
        "correlation_id": uuid4(),
        "clock": _CLOCK,
    }
    kwargs.update(overrides)
    start_tally(fx.tally_store, fx.audit_store, **kwargs)  # type: ignore[arg-type]
    return tally_id


def _started_and_completed(fx: _Fixture, *, result_data: dict[str, int] | None = None) -> UUID:
    tally_id = _start(fx)
    complete_tally(
        fx.tally_store,
        fx.audit_store,
        tally_id=tally_id,
        result_data=result_data if result_data is not None else {"yes": 6, "no": 4},
        invalid_vote_count=0,
        tally_signature=None,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return tally_id


def _verified(fx: _Fixture, *, result_data: dict[str, int] | None = None) -> UUID:
    tally_id = _started_and_completed(fx, result_data=result_data)
    verify_tally(
        fx.tally_store,
        fx.audit_store,
        tally_id=tally_id,
        verification_passed=True,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return tally_id


# --- start_tally --------------------------------------------------------------


def test_start_tally_creates_running_tally_and_audits() -> None:
    fx = _Fixture()
    tally_id = uuid4()
    result = start_tally(
        fx.tally_store,
        fx.audit_store,
        tally_id=tally_id,
        ballot_id=uuid4(),
        input_set_hash="a" * 64,
        algorithm_version="1.0",
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.tally.verification_status == TallyVerificationStatus.RUNNING
    assert result.event.event_type == "tally.started"
    assert fx.audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_start_tally_without_permission_is_denied() -> None:
    fx = _Fixture()
    with pytest.raises(PermissionDeniedError):
        start_tally(
            fx.tally_store,
            fx.audit_store,
            tally_id=uuid4(),
            ballot_id=uuid4(),
            input_set_hash="a" * 64,
            algorithm_version="1.0",
            actor=_actor(),
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_start_tally_is_idempotent_for_same_event_id_and_content() -> None:
    fx = _Fixture()
    tally_id = uuid4()
    event_id = uuid4()
    correlation_id = uuid4()
    kwargs: dict[str, object] = {
        "tally_id": tally_id,
        "ballot_id": uuid4(),
        "input_set_hash": "a" * 64,
        "algorithm_version": "1.0",
        "actor": _actor(),
        "actor_is_authorized": True,
        "correlation_id": correlation_id,
        "clock": _CLOCK,
        "event_id": event_id,
    }
    first = start_tally(fx.tally_store, fx.audit_store, **kwargs)  # type: ignore[arg-type]
    second = start_tally(fx.tally_store, fx.audit_store, **kwargs)  # type: ignore[arg-type]
    assert first.tally == second.tally
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id


# --- complete_tally -------------------------------------------------------------


def test_complete_tally_records_result_and_audits() -> None:
    fx = _Fixture()
    tally_id = _start(fx)
    result = complete_tally(
        fx.tally_store,
        fx.audit_store,
        tally_id=tally_id,
        result_data={"yes": 6, "no": 4},
        invalid_vote_count=1,
        tally_signature="sig",
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.tally.verification_status == TallyVerificationStatus.COMPLETED
    assert dict(result.tally.result_data) == {"yes": 6, "no": 4}
    assert result.tally.invalid_vote_count == 1
    assert result.event.event_type == "tally.completed"
    assert fx.audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_complete_tally_unknown_tally_raises() -> None:
    fx = _Fixture()
    with pytest.raises(UnknownTallyError):
        complete_tally(
            fx.tally_store,
            fx.audit_store,
            tally_id=uuid4(),
            result_data={},
            invalid_vote_count=0,
            tally_signature=None,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_complete_tally_replay_with_same_content_is_idempotent() -> None:
    fx = _Fixture()
    tally_id = _start(fx)
    kwargs: dict[str, object] = dict(
        tally_id=tally_id,
        result_data={"yes": 6, "no": 4},
        invalid_vote_count=0,
        tally_signature=None,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    first = complete_tally(fx.tally_store, fx.audit_store, **kwargs)  # type: ignore[arg-type]
    second = complete_tally(fx.tally_store, fx.audit_store, **kwargs)  # type: ignore[arg-type]
    assert first.tally == second.tally


def test_complete_tally_replay_with_different_content_conflicts() -> None:
    fx = _Fixture()
    tally_id = _start(fx)
    complete_tally(
        fx.tally_store,
        fx.audit_store,
        tally_id=tally_id,
        result_data={"yes": 6, "no": 4},
        invalid_vote_count=0,
        tally_signature=None,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    with pytest.raises(ForbiddenTallyTransitionError):
        complete_tally(
            fx.tally_store,
            fx.audit_store,
            tally_id=tally_id,
            result_data={"yes": 7, "no": 4},
            invalid_vote_count=0,
            tally_signature=None,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# --- verify_tally ---------------------------------------------------------------


def test_verify_tally_success_emits_event_and_audits() -> None:
    fx = _Fixture()
    tally_id = _started_and_completed(fx)
    result = verify_tally(
        fx.tally_store,
        fx.audit_store,
        tally_id=tally_id,
        verification_passed=True,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.tally.verification_status == TallyVerificationStatus.VERIFIED
    assert result.event is not None
    assert result.event.event_type == "tally.verified"
    audit = fx.audit_store.get_by_event_id(result.audit_event.audit_event_id)
    assert audit is not None
    assert audit.reason_code == "TALLY_STATUS_CHANGED"


def test_verify_tally_failure_emits_no_event_but_audits_integrity_check_failed() -> None:
    """Canon events section 20.10 gives no event name for a failed
    verification - `verify_tally`'s own `event` result must be `None`, but
    the audit trail (`INTEGRITY_CHECK_FAILED`) must still exist."""
    fx = _Fixture()
    tally_id = _started_and_completed(fx)
    result = verify_tally(
        fx.tally_store,
        fx.audit_store,
        tally_id=tally_id,
        verification_passed=False,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.tally.verification_status == TallyVerificationStatus.VERIFICATION_FAILED
    assert result.event is None
    audit = fx.audit_store.get_by_event_id(result.audit_event.audit_event_id)
    assert audit is not None
    assert audit.reason_code == "INTEGRITY_CHECK_FAILED"


def test_verify_tally_unknown_tally_raises() -> None:
    fx = _Fixture()
    with pytest.raises(UnknownTallyError):
        verify_tally(
            fx.tally_store,
            fx.audit_store,
            tally_id=uuid4(),
            verification_passed=True,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_verify_tally_without_permission_is_denied() -> None:
    fx = _Fixture()
    tally_id = _started_and_completed(fx)
    with pytest.raises(PermissionDeniedError):
        verify_tally(
            fx.tally_store,
            fx.audit_store,
            tally_id=tally_id,
            verification_passed=True,
            actor=_actor(),
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# --- publish_result ---------------------------------------------------------


def _publish(
    fx: _Fixture,
    *,
    tally_id: UUID,
    ballot_id: UUID,
    option_counts: dict[str, int],
    accepted_vote_count: int,
    quorum_threshold: int | None,
    challenge_window_hours: int | None = None,
) -> PublishResultResult:
    return publish_result(
        fx.tally_store,
        fx.result_store,
        fx.audit_store,
        result_publication_id=uuid4(),
        ballot_id=ballot_id,
        tally_id=tally_id,
        eligible_count=100,
        credential_count=90,
        accepted_vote_count=accepted_vote_count,
        rejected_vote_count=5,
        quorum_threshold=quorum_threshold,
        option_counts=option_counts,
        challenge_window_hours=challenge_window_hours,
        audit_package_reference="audit-package-1",
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )


def test_publish_result_from_verified_tally_emits_event_and_audits() -> None:
    fx = _Fixture()
    ballot_id = uuid4()
    tally_id = _verified(fx, result_data={"yes": 60, "no": 40})
    # patch ballot_id onto the stored tally so publish_result's cross-check passes
    stored = fx.tally_store.get(tally_id)
    assert stored is not None
    from dataclasses import replace

    fx.tally_store.save(replace(stored, ballot_id=ballot_id))

    result = _publish(
        fx,
        tally_id=tally_id,
        ballot_id=ballot_id,
        option_counts={"yes": 60, "no": 40},
        accepted_vote_count=100,
        quorum_threshold=None,
    )
    assert result.result.quorum_result == QuorumResult.NOT_REQUIRED
    assert result.result.threshold_result == ThresholdResult.THRESHOLD_MET
    assert result.event.event_type == "result.published"
    audit = fx.audit_store.get_by_event_id(result.audit_event.audit_event_id)
    assert audit is not None
    assert audit.reason_code == "RESULT_PUBLISHED"


def test_publish_result_requires_verified_tally() -> None:
    fx = _Fixture()
    ballot_id = uuid4()
    tally_id = _started_and_completed(fx)  # only 'completed', not 'verified'
    stored = fx.tally_store.get(tally_id)
    assert stored is not None
    from dataclasses import replace

    fx.tally_store.save(replace(stored, ballot_id=ballot_id))
    with pytest.raises(ForbiddenTallyTransitionError):
        _publish(
            fx,
            tally_id=tally_id,
            ballot_id=ballot_id,
            option_counts={"yes": 6, "no": 4},
            accepted_vote_count=10,
            quorum_threshold=None,
        )


def test_publish_result_tie_produces_tie_no_decision_and_classification_code() -> None:
    """The dedicated end-to-end proof (application layer) that a tied
    tally publishes with `threshold_result = tie_no_decision`, and that
    the audit trail uses the additive `TALLY_THRESHOLD_TIE_NO_DECISION`
    classification code - never a silently-chosen winner."""
    fx = _Fixture()
    ballot_id = uuid4()
    tally_id = _verified(fx, result_data={"yes": 50, "no": 50})
    stored = fx.tally_store.get(tally_id)
    assert stored is not None
    from dataclasses import replace

    fx.tally_store.save(replace(stored, ballot_id=ballot_id))

    result = _publish(
        fx,
        tally_id=tally_id,
        ballot_id=ballot_id,
        option_counts={"yes": 50, "no": 50},
        accepted_vote_count=100,
        quorum_threshold=None,
    )
    assert result.result.threshold_result == ThresholdResult.TIE_NO_DECISION
    audit = fx.audit_store.get_by_event_id(result.audit_event.audit_event_id)
    assert audit is not None
    assert audit.reason_code == "TALLY_THRESHOLD_TIE_NO_DECISION"


def test_publish_result_quorum_not_met_classification_code() -> None:
    fx = _Fixture()
    ballot_id = uuid4()
    tally_id = _verified(fx, result_data={"yes": 6, "no": 4})
    stored = fx.tally_store.get(tally_id)
    assert stored is not None
    from dataclasses import replace

    fx.tally_store.save(replace(stored, ballot_id=ballot_id))

    result = _publish(
        fx,
        tally_id=tally_id,
        ballot_id=ballot_id,
        option_counts={"yes": 6, "no": 4},
        accepted_vote_count=10,
        quorum_threshold=50,
    )
    assert result.result.quorum_result == QuorumResult.QUORUM_NOT_MET
    audit = fx.audit_store.get_by_event_id(result.audit_event.audit_event_id)
    assert audit is not None
    assert audit.reason_code == "TALLY_QUORUM_NOT_MET"


def test_publish_result_quorum_optional_none_is_not_required() -> None:
    """ADR-009 item 5: quorum is optional per ballot - `None` threshold
    must resolve to `NOT_REQUIRED`, never `QUORUM_NOT_MET`."""
    fx = _Fixture()
    ballot_id = uuid4()
    tally_id = _verified(fx, result_data={"yes": 1, "no": 0})
    stored = fx.tally_store.get(tally_id)
    assert stored is not None
    from dataclasses import replace

    fx.tally_store.save(replace(stored, ballot_id=ballot_id))

    result = _publish(
        fx,
        tally_id=tally_id,
        ballot_id=ballot_id,
        option_counts={"yes": 1, "no": 0},
        accepted_vote_count=1,
        quorum_threshold=None,
    )
    assert result.result.quorum_result == QuorumResult.NOT_REQUIRED


def test_publish_result_computes_challenge_deadline_with_default_window() -> None:
    fx = _Fixture()
    ballot_id = uuid4()
    tally_id = _verified(fx, result_data={"yes": 1, "no": 0})
    stored = fx.tally_store.get(tally_id)
    assert stored is not None
    from dataclasses import replace

    fx.tally_store.save(replace(stored, ballot_id=ballot_id))

    result = _publish(
        fx,
        tally_id=tally_id,
        ballot_id=ballot_id,
        option_counts={"yes": 1, "no": 0},
        accepted_vote_count=1,
        quorum_threshold=None,
        challenge_window_hours=None,
    )
    assert result.result.challenge_deadline_at == _NOW + timedelta(hours=72)


def test_publish_result_without_permission_is_denied() -> None:
    fx = _Fixture()
    ballot_id = uuid4()
    tally_id = _verified(fx)
    stored = fx.tally_store.get(tally_id)
    assert stored is not None
    from dataclasses import replace

    fx.tally_store.save(replace(stored, ballot_id=ballot_id))
    with pytest.raises(PermissionDeniedError):
        publish_result(
            fx.tally_store,
            fx.result_store,
            fx.audit_store,
            result_publication_id=uuid4(),
            ballot_id=ballot_id,
            tally_id=tally_id,
            eligible_count=100,
            credential_count=90,
            accepted_vote_count=80,
            rejected_vote_count=5,
            quorum_threshold=None,
            option_counts={"yes": 6, "no": 4},
            challenge_window_hours=None,
            audit_package_reference="audit-package-1",
            actor=_actor(),
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# --- ADR-008 item 3: no PACK-03<->PACK-03 import ----------------------------


def test_package_never_imports_epd2_voting_service() -> None:
    """Structural proof of ADR-008 item 3: `tally-service` never imports
    `epd2_voting_service` (or any other PACK-03 sibling package) anywhere
    in its own source - a tally is built only from plain, caller-supplied
    parameters, mirroring `epd2_voting_service`'s own
    `test_no_code_path_resolves_a_vote_envelope_to_an_account` structural
    check.
    """
    import epd2_tally_service

    package_dir = Path(inspect.getfile(epd2_tally_service)).parent
    forbidden_modules = {
        "epd2_voting_service",
        "epd2_deliberation_service",
        "epd2_moderation_service",
        "epd2_initiative_service",
        "epd2_delegation_service",
    }

    for py_file in package_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in forbidden_modules, (
                        f"{py_file.name} imports forbidden PACK-03 sibling module {alias.name!r}"
                    )
            elif isinstance(node, ast.ImportFrom):
                assert node.module is not None
                assert node.module.split(".")[0] not in forbidden_modules, (
                    f"{py_file.name} imports from forbidden PACK-03 sibling module {node.module!r}"
                )


def test_package_only_depends_on_epd2_core_and_audit_core() -> None:
    """Every third-party-looking absolute import in this package's own
    source must resolve to `epd2_core` or `epd2_audit_core` - never
    another PACK-02 or PACK-03 service (ADR-008)."""
    import epd2_tally_service

    package_dir = Path(inspect.getfile(epd2_tally_service)).parent
    allowed_prefixes = {"epd2_core", "epd2_audit_core", "epd2_tally_service"}

    for py_file in package_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top.startswith("epd2"):
                        assert top in allowed_prefixes, f"{py_file.name} imports {alias.name!r}"
            elif isinstance(node, ast.ImportFrom):
                assert node.module is not None
                top = node.module.split(".")[0]
                if top.startswith("epd2"):
                    assert top in allowed_prefixes, f"{py_file.name} imports from {node.module!r}"
