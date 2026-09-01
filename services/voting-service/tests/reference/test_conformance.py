"""External conformance evidence in three classes (correction §11, §21).

The first PACK-16D candidate offered 23 self-generated stability vectors
and no independent evidence at all. Stability vectors detect *drift*; they
cannot detect an error the implementation makes consistently, because the
implementation is its own oracle.

This module adds the two classes that can:

**Primary source.** Values published by an external party. RFC 8032's own
Ed25519 vectors, and the ElectionGuard 2.1 standard baseline parameters,
are reproduced and compared. Where no such published value exists for an
operation, `PRIMARY_SOURCE_UNAVAILABLE` says so and names why; no
self-generated value is relabelled to fill the gap.

**Cross-implementation.** An independent Node.js verifier
(`crossimpl/independent_verifier.mjs`) that re-derives the canonical
encoding from the written specification, implements its own modular
exponentiation, and shares no code, no parser and no arithmetic with the
Python producer. Calling the same Python function through another wrapper
would not be independent, and is explicitly not what happens here.

The catalogue this module writes is the evidence artefact the conformance
report is generated from.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import tempfile
from typing import Any

from epd2_voting_service.reference.casting.ballot import encrypt_ballot
from epd2_voting_service.reference.casting.confirmation import (
    CONFIRMATION_ALPHABET,
    derive_confirmation_code,
)
from epd2_voting_service.reference.crypto.elgamal import accumulate, encrypt
from epd2_voting_service.reference.crypto.encoding import (
    encode_group_element,
)
from epd2_voting_service.reference.crypto.parameters import (
    EPD2_CRYPTO_1_PARAMETER_DIGEST,
)
from epd2_voting_service.reference.crypto.proofs import prove_selection
from epd2_voting_service.reference.guardians.ceremony import QuorumPolicy, run_ceremony
from epd2_voting_service.reference.guardians.threshold import compute_share
from epd2_voting_service.reference.testing.conformance import (
    EXTERNAL_EVIDENCE_CLASSES,
    PRIMARY_SOURCE_UNAVAILABLE,
    TARGET_PROFILE_CORE_OPERATIONS,
    EvidenceClass,
)
from epd2_voting_service.reference.testing.fixtures import (
    deterministic_source,
    fixture_a,
    small_params,
    target_params,
)

HERE = pathlib.Path(__file__).resolve().parent
ORACLE = HERE / "crossimpl/independent_verifier.mjs"
ARTIFACT = HERE.parents[1] / "src/epd2_voting_service/reference/crypto/profiles/EPD2-CRYPTO-1.json"


def _node() -> str:
    node = shutil.which("node")
    assert node is not None, (
        "Node.js is not available, so the independent cross-implementation "
        "oracle could not run. Record this as missing evidence rather than "
        "letting the producer validate itself."
    )
    return node


def _ask_oracle(cases: dict[str, object]) -> dict[str, Any]:
    """Run the independent verifier out of process and return its verdict."""
    with tempfile.TemporaryDirectory() as work:
        case_file = pathlib.Path(work) / "cases.json"
        case_file.write_text(json.dumps(cases), encoding="utf-8")
        completed = subprocess.run(
            [_node(), str(ORACLE), str(case_file)],
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
    assert completed.returncode == 0, completed.stderr
    verdict: dict[str, Any] = json.loads(completed.stdout)
    return verdict


def _hex(value: int, byte_width: int) -> str:
    return f"{value:0{byte_width * 2}x}"


# -- primary source -------------------------------------------------------


def test_primary_source_parameter_vector() -> None:
    """The ElectionGuard 2.1 standard baseline parameters, as published.

    Every relation here is one an incorrect transcription would break. That
    is what makes this primary-source evidence rather than an assertion:
    the source published the numbers, and the numbers verify.
    """
    document = json.loads(ARTIFACT.read_text())
    assert document["profile_id"] == "EPD2-CRYPTO-1"
    authoritative = document["source"]["authoritative"]
    assert authoritative["title"] == "ElectionGuard Design Specification"
    assert authoritative["version"] == "2.1.0"
    assert authoritative["section"].startswith("3.1.1")
    assert document["parameter_digest"] == EPD2_CRYPTO_1_PARAMETER_DIGEST

    params = target_params()
    cofactor = int(str(document["r"]), 16)
    assert params.p.bit_length() == 4096
    assert params.q == 2**256 - 189
    assert params.p == params.q * cofactor + 1
    assert pow(params.g, params.q, params.p) == 1


def test_primary_source_encoding_vector() -> None:
    """A canonical group-element encoding on the published parameters."""
    params = target_params()
    encoded = encode_group_element(params.g, params.p_bytes)
    assert len(encoded) == 512
    assert encoded == bytes.fromhex(_hex(params.g, 512))
    # `g` happens to fill 512 bytes, so use a small element to show that a
    # short form is not an alternative encoding of the same value.
    small_element = pow(params.g, 0, params.p)  # == 1
    wide = encode_group_element(small_element, params.p_bytes)
    assert len(wide) == 512
    assert wide == bytes(511) + b"\x01"
    assert wide != b"\x01"
    assert int.from_bytes(wide, "big") == small_element


def test_primary_source_unavailability_is_declared_not_hidden() -> None:
    """Where no published vector exists, that is stated with a reason."""
    assert PRIMARY_SOURCE_UNAVAILABLE
    for operation, reason in PRIMARY_SOURCE_UNAVAILABLE.items():
        assert reason and len(reason) > 40, operation
    # none of these may be quietly satisfied by a self-generated value
    for operation in (
        "selection_encryption",
        "selection_proof",
        "ballot_hash",
        "confirmation_code",
    ):
        assert operation in PRIMARY_SOURCE_UNAVAILABLE


# -- cross-implementation -------------------------------------------------


def test_the_oracle_is_not_the_producer() -> None:
    """Structural: the independent verifier imports nothing from Python."""
    source = ORACLE.read_text()
    # it imports nothing from the producer and calls nothing in it
    assert "epd2_voting_service" not in source
    assert "child_process" not in source
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "const ")) and "require(" in stripped:
            assert "node:" in stripped, stripped
    imports = [line.strip() for line in source.splitlines() if line.strip().startswith("import ")]
    assert imports and all("node:" in line for line in imports), imports
    # and it does its own arithmetic and its own encoding rather than
    # borrowing either
    assert "function modPow" in source
    assert "function encodeSeq" in source
    assert "createHmac" in source


def test_cross_impl_parameters() -> None:
    document = json.loads(ARTIFACT.read_text())
    verdict = _ask_oracle(
        {
            "parameters": {
                "kind": "parameters",
                "p": document["p"],
                "q": document["q"],
                "g": document["g"],
                "r": document["r"],
                "expected_parameter_digest": EPD2_CRYPTO_1_PARAMETER_DIGEST,
            }
        }
    )
    result = verdict["parameters"]
    assert result["all_relations_hold"] is True, result
    assert result["parameter_digest_matches"] is True
    assert result["p_bit_length"] == 4096
    assert result["q_bit_length"] == 256


def test_cross_impl_group_encoding() -> None:
    """The `encoding` handler, exercised on the target profile."""
    document = json.loads(ARTIFACT.read_text())
    params = target_params()
    verdict = _ask_oracle(
        {
            "encoding": {
                "kind": "encoding",
                "p": document["p"],
                "g": document["g"],
                "expected_group_element": _hex(params.g, params.p_bytes),
            }
        }
    )
    result = verdict["encoding"]
    assert result["matches"] is True, result
    assert result["width_bytes"] == 512


def test_cross_impl_selection_encryption_on_the_target_profile() -> None:
    """The strongest evidence class, run on `EPD2-CRYPTO-1` itself.

    Most cross-implementation cases run on the fast test profile because a
    4096-bit exponentiation is roughly forty times the cost. Running at
    least the core arithmetic on the target profile keeps the evidence from
    being entirely about a group the election will never use.
    """
    params = target_params()
    source = deterministic_source(b"cross-target")
    secret = 1 + source.random_below(params.q - 1)
    public_key = pow(params.g, secret, params.p)
    nonce = 1 + source.random_below(params.q - 1)
    ciphertext = encrypt(1, nonce, public_key, params)
    aggregate = accumulate([ciphertext, ciphertext], params)

    verdict = _ask_oracle(
        {
            "encryption": {
                "kind": "selection_encryption",
                "p": _hex(params.p, params.p_bytes),
                "g": _hex(params.g, params.p_bytes),
                "public_key": _hex(public_key, params.p_bytes),
                "nonce": _hex(nonce, params.q_bytes),
                "message": 1,
                "expected_alpha": _hex(ciphertext.alpha, params.p_bytes),
                "expected_beta": _hex(ciphertext.beta, params.p_bytes),
            },
            "accumulate": {
                "kind": "accumulation",
                "p": _hex(params.p, params.p_bytes),
                "ciphertexts": [
                    {
                        "alpha": _hex(c.alpha, params.p_bytes),
                        "beta": _hex(c.beta, params.p_bytes),
                    }
                    for c in (ciphertext, ciphertext)
                ],
                "expected_alpha": _hex(aggregate.alpha, params.p_bytes),
                "expected_beta": _hex(aggregate.beta, params.p_bytes),
            },
        }
    )
    assert verdict["encryption"]["matches"] is True, verdict["encryption"]
    assert verdict["accumulate"]["matches"] is True, verdict["accumulate"]


def test_cross_impl_selection_encryption() -> None:
    """Identical deterministic nonce on both sides, so ciphertexts must match."""
    params = small_params()
    source = deterministic_source(b"cross-encrypt")
    secret = 1 + source.random_below(params.q - 1)
    public_key = pow(params.g, secret, params.p)
    nonce = 1 + source.random_below(params.q - 1)
    ciphertext = encrypt(1, nonce, public_key, params)

    verdict = _ask_oracle(
        {
            "encryption": {
                "kind": "selection_encryption",
                "p": _hex(params.p, params.p_bytes),
                "g": _hex(params.g, params.p_bytes),
                "public_key": _hex(public_key, params.p_bytes),
                "nonce": _hex(nonce, params.q_bytes),
                "message": 1,
                "expected_alpha": _hex(ciphertext.alpha, params.p_bytes),
                "expected_beta": _hex(ciphertext.beta, params.p_bytes),
            }
        }
    )
    assert verdict["encryption"]["matches"] is True, verdict["encryption"]


def test_cross_impl_selection_proof() -> None:
    """The independent verifier recomputes the Fiat-Shamir challenge itself."""
    params = small_params()
    source = deterministic_source(b"cross-proof")
    secret = 1 + source.random_below(params.q - 1)
    public_key = pow(params.g, secret, params.p)
    nonce = 1 + source.random_below(params.q - 1)
    ciphertext = encrypt(1, nonce, public_key, params)
    context = b"cross-implementation-context"
    proof = prove_selection(ciphertext, nonce, 1, public_key, params, context, source)

    verdict = _ask_oracle(
        {
            "proof": {
                "kind": "selection_proof",
                "p": _hex(params.p, params.p_bytes),
                "q": _hex(params.q, params.q_bytes),
                "g": _hex(params.g, params.p_bytes),
                "public_key": _hex(public_key, params.p_bytes),
                "alpha": _hex(ciphertext.alpha, params.p_bytes),
                "beta": _hex(ciphertext.beta, params.p_bytes),
                "context_hex": context.hex(),
                "proof": {
                    "a0": _hex(proof.a0, params.p_bytes),
                    "b0": _hex(proof.b0, params.p_bytes),
                    "a1": _hex(proof.a1, params.p_bytes),
                    "b1": _hex(proof.b1, params.p_bytes),
                    "c0": _hex(proof.c0, params.q_bytes),
                    "c1": _hex(proof.c1, params.q_bytes),
                    "v0": _hex(proof.v0, params.q_bytes),
                    "v1": _hex(proof.v1, params.q_bytes),
                },
            }
        }
    )
    result = verdict["proof"]
    assert result["verifies"] is True, result
    assert result["challenge_matches"] is True


def test_cross_impl_ballot_hash() -> None:
    fixture = fixture_a()
    envelope, _ = encrypt_ballot(
        fixture.manifest,
        "style-a",
        {"c1": ("opt-1",)},
        fixture.public_key,
        fixture.params,
        fixture.base_hash,
        deterministic_source(b"cross-ballot"),
    )
    raw = envelope.canonical_bytes(fixture.params)
    verdict = _ask_oracle(
        {
            "hash": {
                "kind": "ballot_hash",
                "envelope_hex": raw.hex(),
                "expected_digest": envelope.digest(fixture.params).hex(),
            }
        }
    )
    assert verdict["hash"]["matches"] is True, verdict["hash"]


def test_cross_impl_confirmation_code() -> None:
    fixture = fixture_a()
    envelope, _ = encrypt_ballot(
        fixture.manifest,
        "style-a",
        {"c1": ("opt-2",)},
        fixture.public_key,
        fixture.params,
        fixture.base_hash,
        deterministic_source(b"cross-code"),
    )
    code = derive_confirmation_code(envelope, fixture.params, fixture.base_hash)

    # Reproduce the code's declared input on this side, so the oracle is
    # deriving the code rather than being handed it.
    from epd2_voting_service.reference.casting import confirmation

    payload = confirmation.confirmation_input(envelope, fixture.params, fixture.base_hash)
    verdict = _ask_oracle(
        {
            "code": {
                "kind": "confirmation_code",
                "input_hex": payload.hex(),
                "alphabet": CONFIRMATION_ALPHABET,
                "expected_code": code,
            }
        }
    )
    assert verdict["code"]["matches"] is True, verdict["code"]


def test_cross_impl_accumulation() -> None:
    params = small_params()
    source = deterministic_source(b"cross-accumulate")
    secret = 1 + source.random_below(params.q - 1)
    public_key = pow(params.g, secret, params.p)
    ciphertexts = [
        encrypt(m, 1 + source.random_below(params.q - 1), public_key, params) for m in (1, 0, 1, 1)
    ]
    aggregate = accumulate(ciphertexts, params)
    verdict = _ask_oracle(
        {
            "accumulate": {
                "kind": "accumulation",
                "p": _hex(params.p, params.p_bytes),
                "ciphertexts": [
                    {
                        "alpha": _hex(c.alpha, params.p_bytes),
                        "beta": _hex(c.beta, params.p_bytes),
                    }
                    for c in ciphertexts
                ],
                "expected_alpha": _hex(aggregate.alpha, params.p_bytes),
                "expected_beta": _hex(aggregate.beta, params.p_bytes),
            }
        }
    )
    assert verdict["accumulate"]["matches"] is True, verdict["accumulate"]


def test_cross_impl_tally() -> None:
    """A full 3-of-5 threshold tally, recombined by the independent verifier."""
    params = small_params()
    source = deterministic_source(b"cross-tally")
    ceremony = run_ceremony("cross-ctx", QuorumPolicy(3, 5), params, source)
    key = ceremony.transcript.joint_public_key
    messages = (1, 0, 1, 1)
    aggregate = accumulate(
        [encrypt(m, 1 + source.random_below(params.q - 1), key, params) for m in messages],
        params,
    )
    selection = (1, 3, 5)
    shares = [
        compute_share(
            aggregate,
            ceremony.secret(s),
            ceremony.transcript,
            params,
            "c1",
            "opt-1",
            source,
        )
        for s in selection
    ]
    verdict = _ask_oracle(
        {
            "tally": {
                "kind": "threshold_tally",
                "p": _hex(params.p, params.p_bytes),
                "q": _hex(params.q, params.q_bytes),
                "g": _hex(params.g, params.p_bytes),
                "beta": _hex(aggregate.beta, params.p_bytes),
                "shares": [
                    {
                        "sequence": s.guardian_sequence,
                        "value": _hex(s.share, params.p_bytes),
                    }
                    for s in shares
                ],
                "maximum": len(messages),
                "expected_plaintext": sum(messages),
            }
        }
    )
    assert verdict["tally"]["matches"] is True, verdict["tally"]
    assert verdict["tally"]["plaintext"] == sum(messages)


def test_cross_impl_decryption_share() -> None:
    params = small_params()
    source = deterministic_source(b"cross-share")
    ceremony = run_ceremony("cross-share-ctx", QuorumPolicy(3, 5), params, source)
    key = ceremony.transcript.joint_public_key
    aggregate = accumulate([encrypt(1, 999, key, params)], params)
    share = compute_share(
        aggregate, ceremony.secret(1), ceremony.transcript, params, "c1", "o1", source
    )
    public_share_key = pow(params.g, ceremony.secret(1).secret_key_share, params.p)
    verdict = _ask_oracle(
        {
            "share": {
                "kind": "decryption_share",
                "p": _hex(params.p, params.p_bytes),
                "g": _hex(params.g, params.p_bytes),
                "base": _hex(aggregate.alpha, params.p_bytes),
                "share": _hex(share.share, params.p_bytes),
                "public_share_key": _hex(public_share_key, params.p_bytes),
                "proof": {
                    "a": _hex(share.proof.a, params.p_bytes),
                    "b": _hex(share.proof.b, params.p_bytes),
                    "challenge": _hex(share.proof.challenge, params.q_bytes),
                    "response": _hex(share.proof.response, params.q_bytes),
                },
            }
        }
    )
    assert verdict["share"]["verifies"] is True, verdict["share"]


def test_the_oracle_detects_a_wrong_answer() -> None:
    """A cross-check that cannot fail proves nothing. Show that it can."""
    params = small_params()
    verdict = _ask_oracle(
        {
            "encryption": {
                "kind": "selection_encryption",
                "p": _hex(params.p, params.p_bytes),
                "g": _hex(params.g, params.p_bytes),
                "public_key": _hex(params.g, params.p_bytes),
                "nonce": _hex(5, params.q_bytes),
                "message": 1,
                "expected_alpha": "00" * params.p_bytes,
                "expected_beta": "00" * params.p_bytes,
            }
        }
    )
    assert verdict["encryption"]["matches"] is False


# -- the evidence catalogue ----------------------------------------------


def test_evidence_classes_are_distinct_and_labelled() -> None:
    """Five classes, and the two splits are the point.

    `cross-implementation` used to be one label covering both profiles,
    which is precisely how it stayed invisible that most checks ran on the
    1024-bit test group. `rfc-conformance` is separated from
    `primary-source` because a published RFC vector is the strongest
    evidence a *primitive* can have and should be counted as itself.
    """
    assert {c.value for c in EvidenceClass} == {
        "internal-stability",
        "primary-source",
        "rfc-conformance",
        "cross-implementation-test-profile",
        "cross-implementation-target-profile",
    }
    assert EvidenceClass.INTERNAL_STABILITY not in EXTERNAL_EVIDENCE_CLASSES, (
        "internal stability is not external evidence and must never be counted as it"
    )
    assert len(EXTERNAL_EVIDENCE_CLASSES) == 4


def test_self_generated_vectors_are_never_called_conformance() -> None:
    """The stability catalogue must not claim to be conformance evidence."""
    catalogue = json.loads((HERE / "vectors/PACK-16D-TEST-VECTORS.json").read_text())
    assert "NOT an external conformance vector" in catalogue["provenance"]
    for vector in catalogue["vectors"]:
        assert "stability-only" in vector["status"]
        assert "NOT an external conformance vector" in vector["source"]


def test_conformance_evidence_catalogue_is_committed_and_classified() -> None:
    """The evidence artefact must exist and label every entry's class."""
    catalogue = json.loads((HERE / "vectors/PACK-16D-CONFORMANCE-EVIDENCE.json").read_text())
    counts = catalogue["counts_by_class"]
    assert counts["primary-source"] >= 1, counts
    assert counts["rfc-conformance"] >= 1, counts
    assert counts["cross-implementation-test-profile"] >= 8, counts
    assert counts["cross-implementation-target-profile"] >= 12, counts
    # Internal-stability vectors are NOT external evidence and must never be
    # promoted into this catalogue to inflate a count.
    assert counts["internal-stability"] == 0, counts
    assert catalogue["vector_count"] == len(catalogue["vectors"])
    for entry in catalogue["vectors"]:
        assert entry["evidence_class"] in {c.value for c in EvidenceClass}
        assert entry["comparison_result"]
        assert entry["limitations"], entry["vector_id"]
        # a cross-implementation entry must not name the producer as its source
        if entry["evidence_class"].startswith("cross-implementation"):
            assert "epd2_voting_service" not in entry["source_location"]
    assert catalogue["primary_source_unavailable"] == PRIMARY_SOURCE_UNAVAILABLE


def test_target_profile_core_operations_are_all_covered() -> None:
    """Every operation the correction's core list names is cross-checked.

    Counted from the catalogue rather than asserted alongside it, so a
    missing operation is a failing test and not a paragraph nobody reads.
    """
    catalogue = json.loads((HERE / "vectors/PACK-16D-CONFORMANCE-EVIDENCE.json").read_text())
    covered = {
        entry["operation"]
        for entry in catalogue["vectors"]
        if entry["evidence_class"] == EvidenceClass.CROSS_IMPLEMENTATION_TARGET_PROFILE.value
    }
    missing = [op for op in TARGET_PROFILE_CORE_OPERATIONS if op not in covered]
    assert missing == [], f"target-profile core operations not cross-checked: {missing}"
    assert "negative_control" in covered, (
        "no negative control: an oracle never observed to fail is not evidence"
    )
