"""CT-00-02 Unknown Status (canon section 27): an unrecognized status
value is never accepted, for every service that owns a status enum."""

from __future__ import annotations

import pytest

from epd2_account_service.domain import parse_status as parse_account_status
from epd2_account_service.exceptions import UnknownAccountStatusError
from epd2_credential_service.domain import parse_status as parse_credential_status
from epd2_credential_service.exceptions import UnknownCredentialStatusError
from epd2_eligibility_service.domain import parse_decision_value
from epd2_eligibility_service.exceptions import UnknownEligibilityDecisionValueError
from epd2_identity_service.domain import parse_status as parse_identity_status
from epd2_identity_service.exceptions import UnknownVerificationStatusError


def test_account_unknown_status_is_rejected() -> None:
    with pytest.raises(UnknownAccountStatusError) as excinfo:
        parse_account_status("not_a_real_status")
    assert excinfo.value.reason_code == "VALIDATION_UNKNOWN_STATUS"


def test_identity_unknown_status_is_rejected() -> None:
    with pytest.raises(UnknownVerificationStatusError) as excinfo:
        parse_identity_status("not_a_real_status")
    assert excinfo.value.reason_code == "VALIDATION_UNKNOWN_STATUS"


def test_eligibility_unknown_decision_value_is_rejected() -> None:
    with pytest.raises(UnknownEligibilityDecisionValueError) as excinfo:
        parse_decision_value("not_a_real_decision")
    assert excinfo.value.reason_code == "VALIDATION_UNKNOWN_STATUS"


def test_credential_unknown_status_is_rejected() -> None:
    with pytest.raises(UnknownCredentialStatusError) as excinfo:
        parse_credential_status("not_a_real_status")
    assert excinfo.value.reason_code == "VALIDATION_UNKNOWN_STATUS"
