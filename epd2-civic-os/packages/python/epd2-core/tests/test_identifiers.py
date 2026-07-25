from uuid import UUID

from epd2_core.identifiers import generate_uuid, is_valid_uuid


def test_generate_uuid_returns_uuid_instance() -> None:
    result = generate_uuid()
    assert isinstance(result, UUID)


def test_generate_uuid_returns_version_4() -> None:
    result = generate_uuid()
    assert result.version == 4


def test_two_consecutive_uuids_differ() -> None:
    first = generate_uuid()
    second = generate_uuid()
    assert first != second


def test_is_valid_uuid_accepts_valid_string() -> None:
    valid = str(generate_uuid())
    assert is_valid_uuid(valid) is True


def test_is_valid_uuid_rejects_invalid_string() -> None:
    assert is_valid_uuid("not-a-uuid") is False


def test_is_valid_uuid_rejects_empty_string() -> None:
    assert is_valid_uuid("") is False


def test_is_valid_uuid_does_not_raise_on_garbage_input() -> None:
    # Should return False, never raise, for malformed input.
    assert is_valid_uuid("12345") is False
    assert is_valid_uuid("uuid-uuid-uuid-uuid") is False
