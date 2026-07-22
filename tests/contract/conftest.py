"""Shared fixtures for the CLAUDE-PACK-02 CT-00 contract-test suite (pack
section 12.1, `docs/canonical/TZ-00-domain-event-canon.md` section 27).

Requires all five services' `src/` on `sys.path` in addition to
`epd2-core` - see `LOCAL_VERIFICATION.md` for the `PYTHONPATH` used to run
this directory.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from epd2_account_service.storage import InMemoryAccountStore
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.storage import InMemoryCredentialStore
from epd2_eligibility_service.storage import (
    InMemoryEligibilityDecisionStore,
    InMemoryEligibilityRuleStore,
    InMemoryEligibilitySnapshotStore,
)
from epd2_identity_service.storage import InMemoryIdentityRecordStore

# Put this directory on sys.path so sibling test modules can
# `from _schema_helpers import ...` as a plain top-level module, without
# requiring `tests/__init__.py` / `tests/contract/__init__.py` (a
# deliberate PACK-01-era choice - see the `--import-mode=importlib`
# comment in the root `pyproject.toml`).
sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 1, 1, tzinfo=UTC))


@pytest.fixture
def actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="service")


@pytest.fixture
def account_store() -> InMemoryAccountStore:
    return InMemoryAccountStore()


@pytest.fixture
def identity_store() -> InMemoryIdentityRecordStore:
    return InMemoryIdentityRecordStore()


@pytest.fixture
def eligibility_rule_store() -> InMemoryEligibilityRuleStore:
    return InMemoryEligibilityRuleStore()


@pytest.fixture
def eligibility_decision_store() -> InMemoryEligibilityDecisionStore:
    return InMemoryEligibilityDecisionStore()


@pytest.fixture
def eligibility_snapshot_store() -> InMemoryEligibilitySnapshotStore:
    return InMemoryEligibilitySnapshotStore()


@pytest.fixture
def credential_store() -> InMemoryCredentialStore:
    return InMemoryCredentialStore()


@pytest.fixture
def audit_store() -> InMemoryAuditEventStore:
    return InMemoryAuditEventStore()
