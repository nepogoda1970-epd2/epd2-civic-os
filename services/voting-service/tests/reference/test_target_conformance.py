"""Target-profile cross-implementation core (final correction §18-§25, §35).

The audit found `CROSS-IMPLEMENTATION ON TARGET PROFILE: PARTIAL`. It was
right: the oracle existed and was useful, but most of what it checked ran on
the 1024-bit test profile, and three operations on `EPD2-CRYPTO-1`. Evidence
about a group the election will never use is evidence about the *code paths*
being independent, not about the numbers being right in the group that
matters.

This module closes that. Every operation in the correction's core list is
cross-checked **on `EPD2-CRYPTO-1` itself**, against the independent Node.js
verifier, from one deterministic fixture set. It also demonstrates the
oracle rejecting a deliberately invalid target-profile fixture, because a
cross-check that has never been observed to fail is not evidence.

**It is slow, and that is not a defect.** A 4096-bit modular exponentiation
costs roughly forty times a 1024-bit one, and the whole point is not to
substitute a cheaper group. The module is marked `slow_conformance` so it
can be run on its own:

    pytest -m slow_conformance services/voting-service/tests/reference/

Timings are recorded per operation and written next to the fixtures, so the
cost is a published number rather than an excuse.

**Independence.** The oracle is a separate process, in a different language,
importing only `node:` builtins. It is handed *canonical exported fixtures* —
field values — and rebuilds the canonical bytes, the Fiat-Shamir challenges
and the group arithmetic itself. It is never handed a digest the producer
computed and asked to agree with it.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
from typing import Any

import pytest

from epd2_voting_service.reference.casting.ballot import encrypt_ballot
from epd2_voting_service.reference.casting.confirmation import (
    CONFIRMATION_ALPHABET,
    derive_confirmation_code,
)
from epd2_voting_service.reference.crypto.elgamal import accumulate, encrypt
from epd2_voting_service.reference.crypto.parameters import (
    EPD2_CRYPTO_1_PARAMETER_DIGEST,
    TARGET_PROFILE_ID,
)
from epd2_voting_service.reference.crypto.proofs import prove_selection
from epd2_voting_service.reference.guardians.ceremony import (
    QuorumPolicy,
    guardian_public_share_key,
    run_ceremony,
)
from epd2_voting_service.reference.guardians.threshold import compute_share
from epd2_voting_service.reference.testing.fixtures import (
    deterministic_source,
    fixture_a,
    target_params,
)

pytestmark = pytest.mark.slow_conformance

HERE = pathlib.Path(__file__).resolve().parent
ORACLE = HERE / "crossimpl/independent_verifier.mjs"
ARTIFACT = HERE.parents[1] / "src/epd2_voting_service/reference/crypto/profiles/EPD2-CRYPTO-1.json"

# INFRA-01 / PACK-25C6-equivalent verification-harness integrity correction:
# the two frozen PACK-16D reference artefacts below are governed, immutable
# *inputs* of the accepted baseline. This module used to write its generated
# fixtures and timings over them, which made test results depend on execution
# order and host conditions and let an ordinary test run mutate accepted
# evidence. Generated material now goes only to an isolated output location
# outside the source tree; the frozen copies are never written by tests.
FROZEN_EXPORT = HERE / "vectors/PACK-16D-TARGET-PROFILE-FIXTURES.json"
FROZEN_TIMINGS = HERE / "vectors/PACK-16D-TARGET-PROFILE-TIMINGS.json"

_OUTPUT_ROOT = pathlib.Path(
    os.environ.get("EPD2_TARGET_CONFORMANCE_OUTPUT_DIR")
    or tempfile.mkdtemp(prefix="epd2-pack16d-target-conformance-")
)
EXPORT = _OUTPUT_ROOT / "PACK-16D-TARGET-PROFILE-FIXTURES.json"
TIMINGS = _OUTPUT_ROOT / "PACK-16D-TARGET-PROFILE-TIMINGS.json"


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_reference_artifacts_are_never_test_outputs() -> None:
    """The frozen PACK-16D artefacts are immutable inputs, not output paths.

    Structural proof that the isolation correction holds: the generated
    output destinations resolve outside the repository's frozen vectors
    directory, and the frozen artefacts still carry the exact accepted
    SHA-256 digests pinned in the governed harness pin list.
    """
    frozen_dir = FROZEN_EXPORT.parent.resolve()
    assert EXPORT.resolve().parent != frozen_dir, "generated fixtures must not target frozen dir"
    assert TIMINGS.resolve().parent != frozen_dir, "generated timings must not target frozen dir"

    pin_file = HERE.parents[3] / "scripts/acceptance/frozen_artifacts.json"
    assert pin_file.is_file(), f"governed frozen-artifact pin list missing: {pin_file}"
    pins = {
        entry["path"]: entry["sha256"] for entry in json.loads(pin_file.read_text())["artifacts"]
    }
    repo_root = HERE.parents[3]
    for frozen in (FROZEN_EXPORT, FROZEN_TIMINGS, ARTIFACT):
        rel = frozen.resolve().relative_to(repo_root.resolve()).as_posix()
        assert rel in pins, f"frozen artefact {rel} is not pinned in the governed pin list"
        assert _sha256(frozen) == pins[rel], f"frozen artefact {rel} no longer matches its pin"


def _node() -> str:
    node = shutil.which("node")
    assert node is not None, (
        "Node.js is not available, so the independent cross-implementation "
        "oracle could not run on the target profile. Record this as missing "
        "evidence rather than letting the producer validate itself."
    )
    return node


def _hex(value: int, byte_width: int) -> str:
    return f"{value:0{byte_width * 2}x}"


def _ask_oracle(cases: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as work:
        case_file = pathlib.Path(work) / "cases.json"
        case_file.write_text(json.dumps(cases), encoding="utf-8")
        completed = subprocess.run(
            [_node(), str(ORACLE), str(case_file)],
            capture_output=True,
            text=True,
            timeout=3600,
            check=False,
        )
    assert completed.returncode == 0, completed.stderr
    verdict: dict[str, Any] = json.loads(completed.stdout)
    return verdict


# -- the fixture set: built once, exported, then cross-checked -----------


@pytest.fixture(scope="module")
def target_fixtures() -> dict[str, Any]:
    """Every target-profile case, from one deterministic seed.

    Randomised operations use **fixed** nonces and a seeded source, because
    comparing two independently randomised ciphertexts proves nothing —
    they would differ for the right reason and there would be no way to
    tell that from differing for the wrong one.
    """
    params = target_params()
    document = json.loads(ARTIFACT.read_text())
    source = deterministic_source(b"target-conformance")
    timings: dict[str, float] = {}

    def timed(name: str, fn: Any) -> Any:
        started = time.perf_counter()
        value = fn()
        timings[name] = round(time.perf_counter() - started, 3)
        return value

    secret = 1 + source.random_below(params.q - 1)
    public_key = pow(params.g, secret, params.p)
    nonce = 1 + source.random_below(params.q - 1)

    ciphertext = timed("selection_encryption", lambda: encrypt(1, nonce, public_key, params))
    context = b"EPD2-CRYPTO-1-target-conformance-context"
    proof = timed(
        "selection_proof_generation",
        lambda: prove_selection(ciphertext, nonce, 1, public_key, params, context, source),
    )
    messages = (1, 0, 1, 1)
    nonces = [1 + source.random_below(params.q - 1) for _ in messages]
    ciphertexts = timed(
        "ballot_ciphertexts",
        lambda: [encrypt(m, n, public_key, params) for m, n in zip(messages, nonces, strict=True)],
    )
    aggregate = timed("accumulation", lambda: accumulate(ciphertexts, params))

    fixture = fixture_a(params)
    envelope, _ = timed(
        "ballot_encryption",
        lambda: encrypt_ballot(
            fixture.manifest,
            "style-a",
            {"c1": ("opt-1",)},
            fixture.public_key,
            params,
            fixture.base_hash,
            deterministic_source(b"target-ballot"),
        ),
    )
    ballot_digest = timed("ballot_hash", lambda: envelope.digest(params))
    code = timed(
        "confirmation_code",
        lambda: derive_confirmation_code(envelope, params, fixture.base_hash),
    )

    ceremony = timed(
        "ceremony_3_of_5",
        lambda: run_ceremony("target-ctx", QuorumPolicy(3, 5), params, source),
    )
    joint_key = ceremony.transcript.joint_public_key
    tally_messages = (1, 0, 1, 1)
    tally_aggregate = accumulate(
        [
            encrypt(m, 1 + source.random_below(params.q - 1), joint_key, params)
            for m in tally_messages
        ],
        params,
    )
    selection = (1, 3, 5)
    shares = timed(
        "threshold_shares",
        lambda: [
            compute_share(
                tally_aggregate,
                ceremony.secret(s),
                ceremony.transcript,
                params,
                "c1",
                "opt-1",
                source,
            )
            for s in selection
        ],
    )
    share_public = guardian_public_share_key(ceremony.transcript, 1, params)

    def envelope_fields() -> dict[str, Any]:
        """The ballot as *fields*, so the oracle rebuilds the encoding itself."""
        return {
            "ballot_id": envelope.ballot_id,
            "election_context_id": envelope.election_context_id,
            "ballot_style_id": envelope.ballot_style_id,
            "parameter_set_id": envelope.parameter_set_id,
            "manifest_digest": envelope.manifest_digest.hex(),
            "contests": [
                {
                    "contest_id": contest.contest_id,
                    "selections": [
                        {
                            "option_id": sel.option_id,
                            "ciphertext": {
                                "alpha": _hex(sel.ciphertext.alpha, params.p_bytes),
                                "beta": _hex(sel.ciphertext.beta, params.p_bytes),
                            },
                            "proof": {
                                "a0": _hex(sel.proof.a0, params.p_bytes),
                                "b0": _hex(sel.proof.b0, params.p_bytes),
                                "a1": _hex(sel.proof.a1, params.p_bytes),
                                "b1": _hex(sel.proof.b1, params.p_bytes),
                                "c0": _hex(sel.proof.c0, params.q_bytes),
                                "c1": _hex(sel.proof.c1, params.q_bytes),
                                "v0": _hex(sel.proof.v0, params.q_bytes),
                                "v1": _hex(sel.proof.v1, params.q_bytes),
                            },
                        }
                        for sel in contest.selections
                    ],
                    "accumulated": {
                        "alpha": _hex(contest.accumulated.alpha, params.p_bytes),
                        "beta": _hex(contest.accumulated.beta, params.p_bytes),
                    },
                    "sum_proof": {
                        "a": _hex(contest.sum_proof.a, params.p_bytes),
                        "b": _hex(contest.sum_proof.b, params.p_bytes),
                        "challenge": _hex(contest.sum_proof.challenge, params.q_bytes),
                        "response": _hex(contest.sum_proof.response, params.q_bytes),
                    },
                }
                for contest in envelope.contests
            ],
        }

    profile = TARGET_PROFILE_ID
    cases: dict[str, Any] = {
        "target-parameter-digest": {
            "kind": "parameters",
            "profile_id": profile,
            "expected": EPD2_CRYPTO_1_PARAMETER_DIGEST,
            "p": document["p"],
            "q": document["q"],
            "g": document["g"],
            "r": document["r"],
            "expected_parameter_digest": EPD2_CRYPTO_1_PARAMETER_DIGEST,
        },
        "target-group-encoding": {
            "kind": "encoding",
            "profile_id": profile,
            "expected": _hex(params.g, params.p_bytes),
            "p": document["p"],
            "g": document["g"],
            "expected_group_element": _hex(params.g, params.p_bytes),
        },
        "target-scalar-encoding": {
            "kind": "scalar_encoding",
            "profile_id": profile,
            "expected": _hex(nonce, params.q_bytes),
            "q": _hex(params.q, params.q_bytes),
            "value": _hex(nonce, params.q_bytes),
            "expected_scalar": _hex(nonce, params.q_bytes),
        },
        "target-selection-encryption": {
            "kind": "selection_encryption",
            "profile_id": profile,
            "expected": _hex(ciphertext.alpha, params.p_bytes),
            "p": _hex(params.p, params.p_bytes),
            "g": _hex(params.g, params.p_bytes),
            "public_key": _hex(public_key, params.p_bytes),
            "nonce": _hex(nonce, params.q_bytes),
            "message": 1,
            "expected_alpha": _hex(ciphertext.alpha, params.p_bytes),
            "expected_beta": _hex(ciphertext.beta, params.p_bytes),
        },
        "target-selection-proof": {
            "kind": "selection_proof",
            "profile_id": profile,
            "expected": "verifies",
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
        },
        "target-ballot-structural": {
            "kind": "ballot_structural",
            "profile_id": profile,
            "expected": ballot_digest.hex(),
            "envelope": envelope_fields(),
            "base_hash": fixture.base_hash.hex(),
            "alphabet": CONFIRMATION_ALPHABET,
            "expected_digest": ballot_digest.hex(),
            "expected_code": code,
        },
        "target-accumulation": {
            "kind": "accumulation",
            "profile_id": profile,
            "expected": _hex(aggregate.alpha, params.p_bytes),
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
        },
        "target-guardian-commitment": {
            "kind": "guardian_commitment",
            "profile_id": profile,
            "expected": _hex(share_public, params.p_bytes),
            "p": _hex(params.p, params.p_bytes),
            "q": _hex(params.q, params.q_bytes),
            "g": _hex(params.g, params.p_bytes),
            "sequence": 1,
            "commitments": [
                [_hex(k, params.p_bytes) for k in record.coefficient_commitments]
                for record in ceremony.transcript.guardians
            ],
            "expected_public_share_key": _hex(share_public, params.p_bytes),
            "expected_joint_public_key": _hex(joint_key, params.p_bytes),
        },
        "target-decryption-share": {
            "kind": "decryption_share",
            "profile_id": profile,
            "expected": "verifies",
            "p": _hex(params.p, params.p_bytes),
            "g": _hex(params.g, params.p_bytes),
            "base": _hex(tally_aggregate.alpha, params.p_bytes),
            "share": _hex(shares[0].share, params.p_bytes),
            "public_share_key": _hex(share_public, params.p_bytes),
            "proof": {
                "a": _hex(shares[0].proof.a, params.p_bytes),
                "b": _hex(shares[0].proof.b, params.p_bytes),
                "challenge": _hex(shares[0].proof.challenge, params.q_bytes),
                "response": _hex(shares[0].proof.response, params.q_bytes),
            },
        },
        "target-3-of-5-tally": {
            "kind": "threshold_tally",
            "profile_id": profile,
            "expected": sum(tally_messages),
            "p": _hex(params.p, params.p_bytes),
            "q": _hex(params.q, params.q_bytes),
            "g": _hex(params.g, params.p_bytes),
            "beta": _hex(tally_aggregate.beta, params.p_bytes),
            "shares": [
                {"sequence": s.guardian_sequence, "value": _hex(s.share, params.p_bytes)}
                for s in shares
            ],
            "maximum": len(tally_messages),
            "expected_plaintext": sum(tally_messages),
        },
    }

    # The deliberately invalid fixture. One share's value is multiplied by
    # `g`, which keeps it inside the subgroup — so it is refused by the
    # mathematics rather than by a cheap range check.
    tampered = list(cases["target-3-of-5-tally"]["shares"])
    tampered[0] = {
        "sequence": tampered[0]["sequence"],
        "value": _hex((shares[0].share * params.g) % params.p, params.p_bytes),
    }
    cases["target-3-of-5-tally-invalid-share"] = {
        **cases["target-3-of-5-tally"],
        "expected": "rejected",
        "shares": tampered,
    }
    cases["target-decryption-share-invalid"] = {
        **cases["target-decryption-share"],
        "expected": "rejected",
        "share": _hex((shares[0].share * params.g) % params.p, params.p_bytes),
    }

    EXPORT.parent.mkdir(parents=True, exist_ok=True)
    EXPORT.write_text(
        json.dumps(
            {
                "catalog_version": "EPD2-TARGET-FIXTURES-1",
                "profile_id": profile,
                "parameter_digest": EPD2_CRYPTO_1_PARAMETER_DIGEST,
                "determinism": (
                    "every nonce, scalar, plaintext, election context, manifest "
                    "and guardian polynomial is fixed by a seeded deterministic "
                    "source; no value here is freshly random"
                ),
                "contains_secret_material": False,
                "case_count": len(cases),
                "cases": cases,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"cases": cases, "timings": timings, "params": params}


@pytest.fixture(scope="module")
def verdict(target_fixtures: dict[str, Any]) -> dict[str, Any]:
    """One oracle run over every target-profile case, timed."""
    started = time.perf_counter()
    result = _ask_oracle(target_fixtures["cases"])
    elapsed = round(time.perf_counter() - started, 3)
    timings = dict(target_fixtures["timings"])
    timings["independent_oracle_full_run"] = elapsed
    TIMINGS.parent.mkdir(parents=True, exist_ok=True)
    TIMINGS.write_text(
        json.dumps(
            {
                "profile_id": TARGET_PROFILE_ID,
                "note": (
                    "producer-side generation and one full independent oracle "
                    "run, in seconds, measured on the build host. A benchmark, "
                    "not a capacity statement."
                ),
                "seconds": timings,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return result


def _ok(verdict: dict[str, Any], name: str) -> dict[str, Any]:
    result: dict[str, Any] = verdict[name]
    assert result.get("error") is None, result
    assert result["profile_id"] == TARGET_PROFILE_ID, result
    assert result["oracle_version"], result
    return result


# -- the core, on EPD2-CRYPTO-1 ------------------------------------------


def test_cross_impl_target_parameter_digest(verdict: dict[str, Any]) -> None:
    result = _ok(verdict, "target-parameter-digest")
    assert result["parameter_digest_matches"] is True, result
    assert result["all_relations_hold"] is True, result
    assert result["p_bit_length"] == 4096
    assert result["q_bit_length"] == 256


def test_cross_impl_target_group_encoding(verdict: dict[str, Any]) -> None:
    result = _ok(verdict, "target-group-encoding")
    assert result["matches"] is True, result
    assert result["width_bytes"] == 512


def test_cross_impl_target_scalar_encoding(verdict: dict[str, Any]) -> None:
    result = _ok(verdict, "target-scalar-encoding")
    assert result["matches"] is True, result
    assert result["width_bytes"] == 32


def test_cross_impl_target_selection_encryption(verdict: dict[str, Any]) -> None:
    """Same fixed nonce on both sides, so a difference means a difference."""
    result = _ok(verdict, "target-selection-encryption")
    assert result["matches"] is True, result


def test_cross_impl_target_selection_proof(verdict: dict[str, Any]) -> None:
    """The oracle recomputes the Fiat-Shamir challenge, then every equation."""
    result = _ok(verdict, "target-selection-proof")
    assert result["challenge_matches"] is True, result
    assert result["eq_g_v0"] and result["eq_k_v0"], result
    assert result["eq_g_v1"] and result["eq_k_v1"], result
    assert result["verifies"] is True, result


def test_cross_impl_target_ballot_hash(verdict: dict[str, Any]) -> None:
    """The oracle rebuilds the canonical bytes before hashing them.

    Handing it the producer's canonical encoding would test the hash and
    not the encoding — and the encoding is where the previous round's real
    defect was found.
    """
    result = _ok(verdict, "target-ballot-structural")
    assert result["ballot_hash_matches"] is True, result
    assert result["canonical_length"] > 0


def test_cross_impl_target_confirmation_code(verdict: dict[str, Any]) -> None:
    result = _ok(verdict, "target-ballot-structural")
    assert result["confirmation_code_matches"] is True, result
    assert len(result["confirmation_code"].split("-")) == 5


def test_cross_impl_target_accumulation(verdict: dict[str, Any]) -> None:
    result = _ok(verdict, "target-accumulation")
    assert result["matches"] is True, result


def test_cross_impl_target_guardian_commitment(verdict: dict[str, Any]) -> None:
    """`g^{s_l}` derived from published commitments alone, independently."""
    result = _ok(verdict, "target-guardian-commitment")
    assert result["matches"] is True, result
    assert result["in_subgroup"] is True, result


def test_cross_impl_target_decryption_share(verdict: dict[str, Any]) -> None:
    result = _ok(verdict, "target-decryption-share")
    assert result["eq_g"] and result["eq_base"], result
    assert result["verifies"] is True, result


def test_cross_impl_target_3_of_5_tally(verdict: dict[str, Any]) -> None:
    """Lagrange combination and plaintext recovery, on the real group."""
    result = _ok(verdict, "target-3-of-5-tally")
    assert result["matches"] is True, result
    assert result["plaintext"] == 3


def test_cross_impl_target_invalid_share_rejected(verdict: dict[str, Any]) -> None:
    """An oracle that has never been seen to fail is not evidence.

    Both invalid fixtures stay **inside the subgroup** — each share is
    multiplied by `g` — so they are refused by the mathematics rather than
    by a cheap structural check that would have caught a random value.
    """
    tally = verdict["target-3-of-5-tally-invalid-share"]
    assert tally.get("error") is None, tally
    assert tally["matches"] is False, tally
    assert tally["plaintext"] != 3

    share = verdict["target-decryption-share-invalid"]
    assert share.get("error") is None, share
    assert share["verifies"] is False, share


# -- the evidence artefacts ----------------------------------------------


def test_target_fixtures_are_exported_and_secret_free(
    target_fixtures: dict[str, Any],
) -> None:
    """The exported fixtures are canonical, deterministic and public-only."""
    document = json.loads(EXPORT.read_text())
    assert document["profile_id"] == TARGET_PROFILE_ID
    assert document["parameter_digest"] == EPD2_CRYPTO_1_PARAMETER_DIGEST
    assert document["contains_secret_material"] is False
    assert document["case_count"] >= 12

    params = target_fixtures["params"]
    blob = EXPORT.read_text()
    # No guardian secret, no polynomial coefficient and no signing key may
    # appear. The nonces are deliberately present: they are what makes the
    # ciphertext comparison meaningful, and they belong to a test fixture.
    ceremony_secret_markers = ("secret_key_share", "coefficients", "private")
    for marker in ceremony_secret_markers:
        assert marker not in blob, f"exported fixtures mention {marker!r}"
    assert str(params.p) not in blob, "decimal integers leaked into a hex artefact"


def test_target_timings_are_recorded(verdict: dict[str, Any]) -> None:
    """Cost is published, not used as a reason to shrink the group."""
    document = json.loads(TIMINGS.read_text())
    seconds = document["seconds"]
    for operation in (
        "selection_encryption",
        "selection_proof_generation",
        "ballot_encryption",
        "ballot_hash",
        "confirmation_code",
        "ceremony_3_of_5",
        "threshold_shares",
        "independent_oracle_full_run",
    ):
        assert operation in seconds, f"no timing recorded for {operation}"
        assert seconds[operation] >= 0.0


def test_oracle_imports_no_producer_code() -> None:
    """Structural proof of independence, not a claim about intent.

    The oracle may import `node:` builtins and nothing else. No Python, no
    EPD² module, no shared encoder, no shell-out to the producer.
    """
    text = ORACLE.read_text(encoding="utf-8")
    imports = [line.strip() for line in text.splitlines() if line.strip().startswith("import ")]
    assert imports, "no import lines found; has the oracle been replaced?"
    for line in imports:
        assert 'from "node:' in line, f"non-builtin import in the oracle: {line}"
    for forbidden in (
        "epd2_voting_service",
        "python",
        "child_process",
        "requests",
        "encode_struct",
    ):
        assert forbidden not in text, f"the oracle references {forbidden!r}"
