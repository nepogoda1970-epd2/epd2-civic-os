"""CT-00-05 Unsupported Event Version (canon section 27): an unknown
major version is never processed."""

from __future__ import annotations

import pytest

from epd2_core.event_envelope import UnsupportedEventVersionError, assert_supported_major_version
from epd2_credential_service.events import SUPPORTED_MAJOR_VERSIONS as CREDENTIAL_MAJORS
from epd2_eligibility_service.events import SUPPORTED_MAJOR_VERSIONS as ELIGIBILITY_MAJORS
from epd2_identity_service.events import SUPPORTED_MAJOR_VERSIONS as IDENTITY_MAJORS


@pytest.mark.parametrize(
    "supported_majors",
    [CREDENTIAL_MAJORS, ELIGIBILITY_MAJORS, IDENTITY_MAJORS, frozenset({1})],
)
def test_unsupported_major_version_is_rejected(supported_majors: frozenset[int]) -> None:
    with pytest.raises(UnsupportedEventVersionError):
        assert_supported_major_version("99.0", supported_majors)


def test_supported_major_version_passes() -> None:
    assert_supported_major_version("1.0", frozenset({1}))


def test_malformed_event_version_is_rejected() -> None:
    from epd2_core.event_envelope import InvalidEventEnvelopeError, parse_major_version

    with pytest.raises(InvalidEventEnvelopeError):
        parse_major_version("not-a-version")
