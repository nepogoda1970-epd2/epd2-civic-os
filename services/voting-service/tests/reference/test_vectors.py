"""Test-vector verification (PACK-16D §38).

The committed catalogue is regenerated and compared byte for byte. A
failure here means one of two things and the message says which: either
the implementation changed a canonical form (encoding, domain separation,
hashing, proof transcript) or the catalogue was edited by hand. Both are
decisions, not merges.

Read the catalogue's own provenance note before treating a pass here as
conformance evidence: these vectors are self-generated and prove stability
only.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

from epd2_voting_service.reference.testing.vectors import (
    CATALOG_VERSION,
    SELF_GENERATED,
    STATUS_STABILITY,
    build_catalog,
    serialize,
)

CATALOG_PATH = pathlib.Path(__file__).parent / "vectors" / "PACK-16D-TEST-VECTORS.json"

REQUIRED_FAMILIES = [
    "parameter validation",
    "group element encoding",
    "scalar encoding",
    "domain-separated hashes",
    "selection encryption",
    "selection proof",
    "contest proof",
    "ballot hash",
    "confirmation code",
    "challenge opening",
    "ciphertext accumulation",
    "decryption share",
    "tally result",
    "batch leaf",
    "cover leaf",
    "batch root",
    "inclusion proof",
    "consistency proof",
    "election-record digest",
    "verification result",
]


def _committed() -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(CATALOG_PATH.read_text())
    return payload


def test_catalog_file_exists_and_is_committed() -> None:
    assert CATALOG_PATH.is_file(), f"missing vector catalogue at {CATALOG_PATH}"
    payload = _committed()
    assert payload["catalog_version"] == CATALOG_VERSION
    assert payload["vector_count"] == len(payload["vectors"])


def test_regenerating_the_catalog_is_byte_identical() -> None:
    regenerated = serialize(build_catalog())
    committed = CATALOG_PATH.read_text()
    assert regenerated == committed, (
        "the regenerated vector catalogue differs from the committed one. "
        "Either a canonical form changed (encoding, domain separation, "
        "hashing or a proof transcript) or the file was edited by hand. "
        "Both need a decision, not a regeneration."
    )


def test_generation_is_deterministic_across_runs() -> None:
    assert serialize(build_catalog()) == serialize(build_catalog())


def test_every_required_family_is_present() -> None:
    families = {v["family"] for v in _committed()["vectors"]}
    missing = [f for f in REQUIRED_FAMILIES if f not in families]
    assert missing == [], f"missing vector families: {missing}"


def test_every_vector_carries_the_seven_required_fields() -> None:
    for vector in _committed()["vectors"]:
        assert set(vector) == {
            "vector_id",
            "family",
            "profile_version",
            "input_canonical_bytes",
            "expected_output",
            "explanation",
            "source",
            "status",
        }
        assert vector["vector_id"]
        assert vector["explanation"]
        assert vector["expected_output"], vector["vector_id"]


def test_vector_ids_are_unique() -> None:
    ids = [v["vector_id"] for v in _committed()["vectors"]]
    assert len(ids) == len(set(ids))


def test_no_vector_claims_interoperability() -> None:
    """The honesty check. A vector must not overstate what it proves."""
    payload = _committed()
    assert payload["provenance"] == SELF_GENERATED
    for vector in payload["vectors"]:
        assert vector["status"] == STATUS_STABILITY
        assert vector["source"] == SELF_GENERATED
        assert "conformance" not in vector["status"].lower().replace(
            "not an external conformance vector", ""
        )


def test_no_vector_uses_a_production_profile() -> None:
    """Every vector runs on a TEST profile; none is labelled production."""
    for vector in _committed()["vectors"]:
        assert vector["profile_version"] in {
            "EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160",
            "EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256",
            "n/a",
        }, vector["vector_id"]
        assert vector["profile_version"] != "EPD2-CRYPTO-1"


@pytest.mark.parametrize("index", range(23))
def test_each_vector_output_is_stable(index: int) -> None:
    regenerated = build_catalog()
    committed = _committed()["vectors"]
    assert regenerated[index].vector_id == committed[index]["vector_id"]
    assert regenerated[index].expected_output == committed[index]["expected_output"]
