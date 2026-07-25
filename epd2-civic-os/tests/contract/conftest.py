"""Shared fixtures for the CLAUDE-PACK-02/PACK-03 CT-00 contract-test
suite (pack section 12.1, `docs/canonical/TZ-00-domain-event-canon.md`
section 27).

Requires all eleven services' `src/` on `sys.path` in addition to
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
from epd2_delegation_service.storage import (
    InMemoryDelegationSnapshotStore,
    InMemoryDelegationStore,
)
from epd2_deliberation_service.storage import (
    InMemoryContributionStore,
    InMemoryDiscussionStore,
)
from epd2_eligibility_service.storage import (
    InMemoryEligibilityDecisionStore,
    InMemoryEligibilityRuleStore,
    InMemoryEligibilitySnapshotStore,
)
from epd2_governance_service.storage import (
    InMemoryGovernanceDecisionStore,
    InMemoryGovernancePolicyStore,
    InMemoryRoleAssignmentStore,
    InMemoryTechnicalChallengeStore,
)
from epd2_identity_service.storage import InMemoryIdentityRecordStore
from epd2_initiative_service.storage import (
    InMemoryAmendmentStore,
    InMemoryInitiativeStore,
    InMemoryInitiativeVersionStore,
    InMemorySourceRecordStore,
    InMemorySupportRecordStore,
)
from epd2_moderation_service.storage import (
    InMemoryAppealStore,
    InMemoryModerationCaseStore,
    InMemoryModerationDecisionStore,
)
from epd2_tally_service.storage import InMemoryResultPublicationStore, InMemoryTallyStore
from epd2_voting_service.storage import (
    InMemoryBallotOptionStore,
    InMemoryBallotStore,
    InMemoryVoteEnvelopeStore,
    InMemoryVoteReceiptStore,
)

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


# ---------------------------------------------------------------------------
# PACK-03 store fixtures (initiative-service, deliberation-service,
# moderation-service, voting-service, tally-service, delegation-service) -
# mirror the PACK-02 fixtures above exactly.
# ---------------------------------------------------------------------------


@pytest.fixture
def initiative_store() -> InMemoryInitiativeStore:
    return InMemoryInitiativeStore()


@pytest.fixture
def initiative_version_store() -> InMemoryInitiativeVersionStore:
    return InMemoryInitiativeVersionStore()


@pytest.fixture
def support_record_store() -> InMemorySupportRecordStore:
    return InMemorySupportRecordStore()


@pytest.fixture
def amendment_store() -> InMemoryAmendmentStore:
    return InMemoryAmendmentStore()


@pytest.fixture
def source_record_store() -> InMemorySourceRecordStore:
    return InMemorySourceRecordStore()


@pytest.fixture
def discussion_store() -> InMemoryDiscussionStore:
    return InMemoryDiscussionStore()


@pytest.fixture
def contribution_store() -> InMemoryContributionStore:
    return InMemoryContributionStore()


@pytest.fixture
def moderation_case_store() -> InMemoryModerationCaseStore:
    return InMemoryModerationCaseStore()


@pytest.fixture
def moderation_decision_store() -> InMemoryModerationDecisionStore:
    return InMemoryModerationDecisionStore()


@pytest.fixture
def appeal_store() -> InMemoryAppealStore:
    return InMemoryAppealStore()


@pytest.fixture
def ballot_store() -> InMemoryBallotStore:
    return InMemoryBallotStore()


@pytest.fixture
def ballot_option_store() -> InMemoryBallotOptionStore:
    return InMemoryBallotOptionStore()


@pytest.fixture
def vote_envelope_store() -> InMemoryVoteEnvelopeStore:
    return InMemoryVoteEnvelopeStore()


@pytest.fixture
def vote_receipt_store() -> InMemoryVoteReceiptStore:
    return InMemoryVoteReceiptStore()


@pytest.fixture
def tally_store() -> InMemoryTallyStore:
    return InMemoryTallyStore()


@pytest.fixture
def result_publication_store() -> InMemoryResultPublicationStore:
    return InMemoryResultPublicationStore()


@pytest.fixture
def delegation_store() -> InMemoryDelegationStore:
    return InMemoryDelegationStore()


@pytest.fixture
def delegation_snapshot_store() -> InMemoryDelegationSnapshotStore:
    return InMemoryDelegationSnapshotStore()


# ---------------------------------------------------------------------------
# PACK-05 store fixtures (governance-service) - mirror the PACK-02/PACK-03
# fixtures above exactly.
# ---------------------------------------------------------------------------


@pytest.fixture
def role_assignment_store() -> InMemoryRoleAssignmentStore:
    return InMemoryRoleAssignmentStore()


@pytest.fixture
def governance_policy_store() -> InMemoryGovernancePolicyStore:
    return InMemoryGovernancePolicyStore()


@pytest.fixture
def governance_decision_store() -> InMemoryGovernanceDecisionStore:
    return InMemoryGovernanceDecisionStore()


@pytest.fixture
def technical_challenge_store() -> InMemoryTechnicalChallengeStore:
    return InMemoryTechnicalChallengeStore()
