"""`EPD2-CRYPTO-1` — the real ElectionGuard 2.1 family (correction §5, §6, §18).

The first PACK-16D candidate could not obtain the published constants and
registered the profile as unavailable. It is now present. These tests check
two different things and it matters which is which:

* that the **constants are the published ones** — established by arithmetic
  that no transcription error survives, not by trusting the fetch; and
* that the **whole crypto stack runs on them**, rather than only the loader.

A 4096-bit modular exponentiation is roughly forty times the cost of the
1024-bit test profile, so this module is the slow one by design. Reducing
the group to make it fast would defeat its entire purpose.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

from epd2_voting_service.reference.casting.ballot import (
    encrypt_ballot,
    verify_ballot_proofs,
)
from epd2_voting_service.reference.casting.confirmation import (
    derive_confirmation_code,
    verify_challenge_opening,
)
from epd2_voting_service.reference.crypto.elgamal import accumulate, encrypt
from epd2_voting_service.reference.crypto.parameters import (
    EPD2_CRYPTO_1_PARAMETER_DIGEST,
    PROFILE_BIT_LENGTHS,
    PROFILE_REGISTRY,
    Q_ELECTIONGUARD_2_1,
    TARGET_PROFILE_ID,
    TEST_ONLY_MARKER,
    ParameterProfileUnavailableError,
    ParameterSet,
    ParameterValidationError,
    ProfileSubstitutionError,
    is_probable_prime,
    is_target_profile,
    load_profile,
    load_target_profile,
    require_target_profile,
    validate_parameter_set,
)
from epd2_voting_service.reference.crypto.proofs import prove_selection, verify_selection
from epd2_voting_service.reference.guardians.ceremony import QuorumPolicy, run_ceremony
from epd2_voting_service.reference.testing.fixtures import (
    deterministic_source,
    small_params,
    target_params,
)

ARTIFACT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "src/epd2_voting_service/reference/crypto/profiles/EPD2-CRYPTO-1.json"
)


def _artifact() -> dict[str, object]:
    document: dict[str, object] = json.loads(ARTIFACT.read_text())
    return document


# -- loading and identity ------------------------------------------------


def test_epd2_crypto_1_loads() -> None:
    params = load_target_profile()
    assert params.parameter_set_id == TARGET_PROFILE_ID
    assert is_target_profile(params.parameter_set_id)
    assert params.production_use_permitted is False


def test_epd2_crypto_1_digest() -> None:
    """The artefact's constants are pinned in code, so editing it is caught."""
    document = _artifact()
    assert document["parameter_digest"] == EPD2_CRYPTO_1_PARAMETER_DIGEST
    params = target_params()
    # The ParameterSet digest is a separate, canonical-encoding digest and is
    # deterministic across runs.
    assert params.digest_hex() == target_params().digest_hex()
    assert len(params.digest_hex()) == 64


def test_epd2_crypto_1_p_bits() -> None:
    params = target_params()
    assert params.p.bit_length() == 4096
    assert PROFILE_BIT_LENGTHS[TARGET_PROFILE_ID] == (4096, 256)


def test_epd2_crypto_1_q_bits() -> None:
    params = target_params()
    assert params.q.bit_length() == 256
    assert params.q == Q_ELECTIONGUARD_2_1 == 2**256 - 189


def test_epd2_crypto_1_subgroup_relation() -> None:
    """`q | p-1` and `p = q*r + 1`, with `r` the published cofactor."""
    params = target_params()
    assert (params.p - 1) % params.q == 0
    cofactor = int(str(_artifact()["r"]), 16)
    assert params.p == params.q * cofactor + 1
    assert params.cofactor == cofactor


def test_epd2_crypto_1_generator_order() -> None:
    params = target_params()
    assert params.g != 1
    assert 1 < params.g < params.p
    assert pow(params.g, params.q, params.p) == 1


def test_epd2_crypto_1_structural_provenance() -> None:
    """The published family's documented shape, checked rather than assumed.

    ElectionGuard derives `p` from `ln(2)` between a leading and trailing
    run of 256 one-bits, and `r/2` is prime. A substitute of the same size
    would not have these properties — the first candidate's test profile
    did not — so they are provenance evidence, not decoration.
    """
    params = target_params()
    assert (params.p >> (4096 - 256)) == (1 << 256) - 1
    assert (params.p & ((1 << 256) - 1)) == (1 << 256) - 1
    assert params.cofactor % 2 == 0
    assert is_probable_prime(params.cofactor // 2)

    middle = (params.p >> 256) & ((1 << 3584) - 1)
    # ln(2) to 3584 bits, computed here: ln 2 = 2*atanh(1/3).
    precision = 3700
    accumulator = 0
    k = 0
    while True:
        term = (1 << precision) // ((2 * k + 1) * 3 ** (2 * k + 1))
        if term == 0:
            break
        accumulator += term
        k += 1
    ln2 = (2 * accumulator) >> (precision - 3584)
    # The published p adds an offset to the low bits so that the whole value
    # is prime with the required structure, so only the leading bits agree —
    # but they agree for 3305 of 3584 bits, which no unrelated number would.
    assert (middle - ln2).bit_length() <= 280
    assert middle >> 280 == ln2 >> 280


# -- provenance: immutable, self-contained, and checkable offline --------
#
# The audit found the previous artefact's provenance "PARTIAL — MUTABLE URL /
# DIGEST NOT IN ARTIFACT", and a following round could not close it because
# this build host reaches neither GitHub nor a package index. The commit and
# the raw-byte digest were obtained on a network-enabled host and are now
# recorded in the artefact, so these tests assert the pin **unconditionally**.
#
# They were deliberately written to hold in both the pinned and the blocked
# state while the blocker was open — a permanently red test trains a reader
# to ignore red. That accommodation is now removed: with the pin recorded,
# a `null` commit is a regression and must fail, not be tolerated.
#
# None of these tests touches the network. The values themselves are
# reconstructed from the published rule without consulting any source at all,
# which remains the strongest statement here: a pin says where bytes came
# from, reconstruction says the bytes are the ones the rule produces.


def _ln2_bits(count: int) -> int:
    """The first `count` fractional bits of ln 2, computed here.

    `ln 2 = 2*atanh(1/3) = 2 * sum_{k>=0} (1/3)^(2k+1)/(2k+1)`. Computed
    rather than tabulated, so the test cannot agree with the artefact by
    sharing a constant with it.
    """
    precision = count + 128
    accumulator = 0
    k = 0
    while True:
        term = (1 << precision) // ((2 * k + 1) * 3 ** (2 * k + 1))
        if term == 0:
            break
        accumulator += term
        k += 1
    return (2 * accumulator) >> (precision - count)


def test_epd2_crypto_1_parameters_reconstruct_offline() -> None:
    """Rebuild every constant from the published rule. No file, no network.

    This is the strongest provenance statement available to this round, and
    it is stronger than a commit pin: a URL tells you where bytes came from,
    this tells you the bytes are the ones the rule produces. `p` is rebuilt
    from `ln 2` plus the recorded low offset; `q` is a closed form; `r` and
    `g` follow from `p`. A single wrong hex digit anywhere fails here.
    """
    document = _artifact()
    derivation = document["derivation"]
    assert isinstance(derivation, dict)
    params = target_params()

    prefix_bits = int(derivation["ln2_prefix_bits"])
    low_bits = int(derivation["delta_low_bit_length"])
    assert prefix_bits + low_bits == 3584
    delta = int(str(derivation["delta_low_hex"]), 16)
    assert delta.bit_length() <= low_bits

    middle = (_ln2_bits(prefix_bits) << low_bits) | delta
    rebuilt_p = (((1 << 256) - 1) << 3840) | (middle << 256) | ((1 << 256) - 1)
    assert rebuilt_p == params.p, "p does not reconstruct from the published rule"

    assert params.q == 2**256 - 189, "q is not the published closed form"
    assert (params.p - 1) // params.q == params.cofactor
    assert pow(2, params.cofactor, params.p) == params.g, "g != 2^r mod p"


def test_epd2_crypto_1_source_commit_present() -> None:
    """The commit pin is recorded, and no excuse for lacking one survives.

    While the pin was unobtainable the artefact carried an `unpinned_reason`
    and an `auditor_action`. Both had to disappear in the same change that
    added the pin: a repository that keeps an excuse next to the thing the
    excuse was for is telling a reader two incompatible stories.
    """
    corroborating = _artifact()["source"]["corroborating"]  # type: ignore[index]
    commit = corroborating["upstream_commit"]
    assert commit, "the corroborating implementation source is not commit-pinned"
    assert corroborating.get("unpinned_reason") in (None, ""), (
        "a commit pin and an excuse for not having one cannot both be true"
    )
    assert corroborating.get("auditor_action") in (None, ""), (
        "the instructions for obtaining the pin outlived the pin itself"
    )
    assert str(corroborating["upstream_commit_date"]), (
        "a commit with no date cannot be placed against the specification release"
    )
    assert str(corroborating["commit_pinned_source_url"]).count(str(commit)) == 1


def test_epd2_crypto_1_source_url_commit_pinned() -> None:
    """Both references are immutable: a versioned asset and a commit."""
    source = _artifact()["source"]
    authoritative = source["authoritative"]  # type: ignore[index]
    url = str(authoritative["document_url"])
    assert "/main/" not in url and "/master/" not in url and "/HEAD/" not in url
    assert "/releases/download/v2.1/" in url, url
    assert authoritative["document_sha256"]

    corroborating = source["corroborating"]  # type: ignore[index]
    pinned = str(corroborating["commit_pinned_source_url"])
    for mutable in ("/main/", "/master/", "/latest/", "/releases/latest/", "/HEAD/"):
        assert mutable not in pinned, f"the pinned URL contains the mutable reference {mutable!r}"


def test_epd2_crypto_1_upstream_commit_nonempty() -> None:
    """A commit is recorded, and it is not a placeholder."""
    corroborating = _artifact()["source"]["corroborating"]  # type: ignore[index]
    commit = corroborating["upstream_commit"]
    assert commit is not None, "upstream_commit is null; the source is unpinned"
    assert str(commit).strip(), "upstream_commit is blank"
    assert str(commit).strip("0"), "an all-zero object id is the null commit, not a pin"
    assert corroborating["provenance_status"].startswith("SATISFIED")


def test_epd2_crypto_1_upstream_commit_is_full_sha() -> None:
    """The commit must be a full 40-hex git object id.

    An abbreviated hash is not a pin: it is a prefix that a future object
    can collide with, and it cannot be fetched unambiguously. Branch and tag
    names are rejected here for the same reason — they move.
    """
    corroborating = _artifact()["source"]["corroborating"]  # type: ignore[index]
    commit = str(corroborating["upstream_commit"])
    assert len(commit) == 40, f"expected a full 40-character commit id, got {len(commit)}"
    assert all(character in "0123456789abcdef" for character in commit), (
        "a commit id must be lower-case hexadecimal"
    )
    assert commit not in ("main", "master", "HEAD", "latest")


def test_epd2_crypto_1_source_url_contains_exact_commit() -> None:
    """The pinned URL must contain the exact commit and the exact path.

    A URL that pins a different commit from the one recorded beside it would
    let the two drift apart silently, and a reader checking the digest would
    be fetching bytes the artefact never claimed anything about.
    """
    corroborating = _artifact()["source"]["corroborating"]  # type: ignore[index]
    commit = str(corroborating["upstream_commit"])
    url = str(corroborating["commit_pinned_source_url"])
    assert commit in url, "the pinned URL does not contain the declared commit"
    assert str(corroborating["source_file_path"]) in url, (
        "the pinned URL does not point at the declared source file"
    )
    assert str(corroborating["upstream_repository"]).removeprefix("https://github.com/") in url


def test_epd2_crypto_1_source_file_path_present() -> None:
    """The digest is meaningless without the file it was taken over.

    `source_sha256` names bytes; `source_file_path` names *which* bytes. A
    digest recorded without the path is unverifiable in practice — an
    auditor cannot know what to hash — so the path is asserted separately
    rather than left implicit in the URL.
    """
    corroborating = _artifact()["source"]["corroborating"]  # type: ignore[index]
    path = corroborating["source_file_path"]
    assert path, "no source_file_path: the recorded digest names no file"
    path = str(path)
    assert not path.startswith("/"), "the path must be repository-relative, not absolute"
    assert ".." not in path.split("/"), "the path must not traverse outside the repository"
    assert path.endswith(".rs"), path
    assert str(corroborating["commit_pinned_source_url"]).endswith(path)


def test_epd2_crypto_1_source_sha256_format() -> None:
    """The upstream file digest must look like a SHA-256."""
    digests: dict[str, object] = _artifact()["digests"]  # type: ignore[assignment]
    digest = str(digests["source_sha256"])
    assert len(digest) == 64, f"expected 64 hex characters, got {len(digest)}"
    assert all(character in "0123456789abcdef" for character in digest), (
        "a digest must be lower-case hexadecimal"
    )
    assert "RECORDED" in str(digests["source_sha256_status"])
    assert "NOT RECORDED" not in str(digests["source_sha256_status"])


def test_epd2_crypto_1_normative_and_corroborating_sources_distinct() -> None:
    """The implementation source is never a stand-in for the specification.

    The hierarchy is declared explicitly rather than left to be inferred
    from field names, because the failure mode is subtle: a reader who
    treats a reference implementation's source file as normative will
    accept a value the specification does not actually publish.
    """
    source = _artifact()["source"]
    authoritative = source["authoritative"]  # type: ignore[index]
    corroborating = source["corroborating"]  # type: ignore[index]
    hierarchy = source["hierarchy"]  # type: ignore[index]

    assert authoritative["is_normative"] is True
    assert corroborating["is_normative"] is False
    assert authoritative["kind"] == "specification"
    assert corroborating["kind"] != "specification"
    assert str(authoritative["document_url"]) != str(corroborating["human_readable_url"])
    assert str(authoritative["document_url"]) != str(corroborating["commit_pinned_source_url"])
    assert "not a substitute" in str(corroborating["role"]).lower()
    for key in ("normative", "corroborating_implementation", "local_immutable_artifact"):
        assert hierarchy[key]
    # Pinning the implementation source does not promote it. The hierarchy
    # must still say the specification is the normative one, because the
    # tempting misreading after a successful pin is "both are now solid, so
    # either will do".
    assert "normative" in str(hierarchy["note"]).lower()
    assert str(authoritative["document_sha256"]) != str(corroborating["source_sha256"])


def test_epd2_crypto_1_specification_sha256_present() -> None:
    """The authoritative document's digest lives **in the artefact**.

    The audit's second complaint was that the digest sat only in an evidence
    register. It is here now, next to the values it vouches for, so the
    artefact is self-contained.
    """
    document = _artifact()
    authoritative = document["source"]["authoritative"]  # type: ignore[index]
    digest = str(authoritative["document_sha256"])
    assert len(digest) == 64 and int(digest, 16) >= 0
    assert authoritative["document_sha256_provenance"], (
        "a digest with no stated provenance is a number, not evidence"
    )
    # And it is a *different* thing from the parameter digest, by name and
    # by definition, so the two can never be quietly swapped.
    digests = document["digests"]
    assert digests["parameter_digest"] != digest  # type: ignore[index]
    assert digests["parameter_digest_definition"] != digests["source_sha256_definition"]  # type: ignore[index]
    assert digests["specification_sha256"] == digest  # type: ignore[index]


def test_epd2_crypto_1_source_sha256_present() -> None:
    """The upstream file's digest is recorded, and says whose word it is on.

    Three digests live in this artefact and they answer three different
    questions. This one is over the corroborating implementation file's raw
    bytes at the pinned commit. It carries an explicit verification scope
    because the build host cannot reach GitHub: the value was produced on a
    network-enabled host, and saying so is the difference between evidence
    and a number that looks like evidence.
    """
    document = _artifact()
    digests: dict[str, object] = document["digests"]  # type: ignore[assignment]
    corroborating = document["source"]["corroborating"]  # type: ignore[index]

    digest = str(digests["source_sha256"])
    assert digest and digest != "None", "no upstream source digest is recorded"
    assert digest == str(corroborating["source_sha256"]), (
        "the digest in `digests` and the one in `source.corroborating` disagree"
    )
    assert digest != str(digests["parameter_digest"]), (
        "the upstream file digest and the parameter digest cannot be the same value"
    )
    assert digest != str(digests["specification_sha256"])

    scope = str(corroborating["source_sha256_verification_scope"])
    assert scope, "a digest with no stated verification scope is a number, not evidence"
    assert "did NOT re-fetch" in scope, (
        "the scope must state plainly that this session did not re-fetch the bytes"
    )
    assert "sha256sum" in scope, "the scope must name the command that closes the gap"


def test_epd2_crypto_1_parameter_digest_recomputes() -> None:
    """`sha256(p||q||g||r)` over the artefact's own hex, recomputed here."""
    document = _artifact()
    recomputed = hashlib.sha256(
        (str(document["p"]) + str(document["q"]) + str(document["g"]) + str(document["r"])).encode()
    ).hexdigest()
    assert recomputed == document["parameter_digest"]
    assert recomputed == EPD2_CRYPTO_1_PARAMETER_DIGEST
    assert recomputed == document["digests"]["parameter_digest"]  # type: ignore[index]


def test_epd2_crypto_1_mutable_branch_not_authoritative() -> None:
    """A `/main/` URL may appear, but never as the thing to rely on.

    Now that a commit-pinned URL exists beside it, the navigation URL is the
    one a hurried reader is most likely to copy. It stays marked, and the
    pinned URL must not be the same string.
    """
    corroborating = _artifact()["source"]["corroborating"]  # type: ignore[index]
    assert corroborating["human_readable_url_is_authoritative"] is False
    assert "/main/" in str(corroborating["human_readable_url"])
    assert corroborating["human_readable_url_note"]
    assert str(corroborating["human_readable_url"]) != str(
        corroborating["commit_pinned_source_url"]
    )

    # No other field in the artefact may carry a mutable reference without
    # being marked, which is what stops the problem reappearing elsewhere.
    blob = json.dumps(_artifact())
    for occurrence in ("/main/", "/master/"):
        if occurrence in blob:
            assert occurrence in str(corroborating["human_readable_url"]), (
                f"an unmarked mutable reference {occurrence!r} appears elsewhere in the artefact"
            )


def test_epd2_crypto_1_profile_id_content_binding() -> None:
    """The id names this content, and the filename names the id."""
    document = _artifact()
    assert document["profile_id"] == TARGET_PROFILE_ID
    assert ARTIFACT.stem == TARGET_PROFILE_ID
    params = target_params()
    assert params.parameter_set_id == document["profile_id"]
    # Binding is by digest, not by string equality of a label: change any
    # constant and the pinned digest no longer matches the id's content.
    assert document["parameter_digest"] == EPD2_CRYPTO_1_PARAMETER_DIGEST
    assert params.p == int(str(document["p"]), 16)
    assert params.q == int(str(document["q"]), 16)
    assert params.g == int(str(document["g"]), 16)
    assert params.cofactor == int(str(document["r"]), 16)


def test_epd2_crypto_1_invalid_constant_rejected(tmp_path: pathlib.Path) -> None:
    """A single altered digit must fail the load, not be absorbed."""
    document = _artifact()
    mutated = dict(document)
    original = str(document["g"])
    mutated["g"] = original[:-1] + ("0" if original[-1] != "0" else "1")
    # its own self-digest no longer matches
    from epd2_voting_service.reference.crypto.parameters import (
        _artifact_parameter_digest,
    )

    assert _artifact_parameter_digest(mutated) != document["parameter_digest"]

    # and the group relation it was chosen to satisfy no longer holds
    params = target_params()
    bad_g = int(str(mutated["g"]), 16)
    assert pow(bad_g, params.q, params.p) != 1

    bad = type(params)(
        parameter_set_id=TARGET_PROFILE_ID,
        profile_version=params.profile_version,
        provenance="",
        production_use_permitted=False,
        p=params.p,
        q=params.q,
        g=bad_g,
    )
    with pytest.raises(ParameterValidationError, match="order-q subgroup"):
        validate_parameter_set(bad, expect_p_bits=4096, expect_q_bits=256, check_primality=False)


def test_epd2_crypto_1_no_fallback() -> None:
    """No path substitutes a test profile for the target."""
    target = target_params()
    for name in PROFILE_REGISTRY:
        if name == TARGET_PROFILE_ID:
            continue
        assert TEST_ONLY_MARKER in name, (
            f"{name} does not carry the test-only marker, so a reader could "
            "mistake it for the target"
        )
        other = load_profile(name, check_primality=False)
        assert other.p != target.p
        assert other.g != target.g
        with pytest.raises(ProfileSubstitutionError, match="never stand in"):
            require_target_profile(other, "a conformance run")
    require_target_profile(target, "a conformance run")

    # an unknown profile is refused rather than defaulted
    with pytest.raises(ParameterProfileUnavailableError):
        load_profile("EPD2-CRYPTO-1-BUT-FASTER")


def test_epd2_crypto_1_no_environment_or_flag_can_substitute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Neither the environment nor a feature flag can redirect the loader."""
    for name in (
        "EPD2_PROFILE",
        "EPD2_PARAMETER_SET",
        "EPD2_VOTING_REFERENCE_TEST_PROFILE",
        "EPD2_CRYPTO_PROFILE_OVERRIDE",
    ):
        monkeypatch.setenv(name, "EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160")
    assert load_target_profile().p.bit_length() == 4096

    from epd2_voting_service.reference.invariants import (
        UnsafeFeatureFlagError,
        enforce_startup_invariants,
    )

    with pytest.raises(UnsafeFeatureFlagError):
        enforce_startup_invariants({"disable_parameter_validation": True})


def test_loader_source_names_no_fallback_branch() -> None:
    """A structural check: the loader has no `except -> substitute` path."""
    import inspect

    from epd2_voting_service.reference.crypto import parameters

    source = inspect.getsource(parameters.load_profile)
    assert "except" not in source
    assert "TESTONLY" not in source
    assert "default" not in source.lower()


# -- the crypto stack, on the real profile -------------------------------


@pytest.fixture(scope="module")
def target() -> ParameterSet:
    return target_params()


def test_epd2_crypto_1_encrypt_verify(target: ParameterSet) -> None:
    params = target
    source = deterministic_source(b"crypto1-encrypt")
    secret = 1 + source.random_below(params.q - 1)
    public_key = pow(params.g, secret, params.p)
    for message in (0, 1):
        nonce = 1 + source.random_below(params.q - 1)
        ciphertext = encrypt(message, nonce, public_key, params)
        proof = prove_selection(
            ciphertext,
            nonce,
            message,
            public_key,
            params,
            b"ctx",
            source,
        )
        assert verify_selection(ciphertext, proof, public_key, params, b"ctx")
        assert not verify_selection(ciphertext, proof, public_key, params, b"other")


def test_epd2_crypto_1_key_generation_and_group_encoding(target: ParameterSet) -> None:
    params = target
    assert params.p_bytes == 512
    assert params.q_bytes == 32
    from epd2_voting_service.reference.crypto.encoding import (
        encode_group_element,
        encode_scalar,
    )

    assert len(encode_group_element(params.g, params.p_bytes)) == 512
    assert len(encode_scalar(7, params.q_bytes)) == 32


def test_epd2_crypto_1_challenge_opening(target: ParameterSet) -> None:
    from epd2_voting_service.reference.testing.fixtures import fixture_a

    fixture = fixture_a(target)
    envelope, opening = encrypt_ballot(
        fixture.manifest,
        "style-a",
        {"c1": ("opt-1",)},
        fixture.public_key,
        fixture.params,
        fixture.base_hash,
        deterministic_source(b"crypto1-ballot"),
    )
    verify_ballot_proofs(
        envelope, fixture.manifest, fixture.public_key, fixture.params, fixture.base_hash
    )
    verify_challenge_opening(
        envelope, opening, fixture.public_key, fixture.params, fixture.base_hash
    )
    code = derive_confirmation_code(envelope, fixture.params, fixture.base_hash)
    assert len(code.split("-")) == 5
    assert envelope.digest(fixture.params)


def test_epd2_crypto_1_homomorphic_tally(target: ParameterSet) -> None:
    params = target
    source = deterministic_source(b"crypto1-tally")
    secret = 1 + source.random_below(params.q - 1)
    public_key = pow(params.g, secret, params.p)
    messages = [1, 0, 1, 1]
    ciphertexts = [
        encrypt(m, 1 + source.random_below(params.q - 1), public_key, params) for m in messages
    ]
    aggregate = accumulate(ciphertexts, params)
    from epd2_voting_service.reference.crypto.elgamal import decode_exponent

    share = pow(aggregate.alpha, secret, params.p)
    group_value = aggregate.beta * pow(share, params.p - 2, params.p) % params.p
    assert decode_exponent(group_value, params, maximum=len(messages)) == sum(messages)


def test_epd2_crypto_1_guardian_ceremony(target: ParameterSet) -> None:
    """A 3-of-5 ceremony on the real parameters, not just the fast profile."""
    from epd2_voting_service.reference.guardians.ceremony import verify_ceremony

    params = target
    result = run_ceremony(
        "crypto1-ceremony",
        QuorumPolicy(3, 5),
        params,
        deterministic_source(b"crypto1-dkg"),
    )
    ok, detail = verify_ceremony(result.transcript, params)
    assert ok, detail


def test_epd2_crypto_1_election_record_verification(target: ParameterSet) -> None:
    """The slowest and most important test here: a whole election, verified.

    Every other test in this module exercises one operation on the real
    parameters. This one runs the entire specified path on them — a 3-of-5
    ceremony, a cast, sealing, closure, a threshold tally and full record
    verification — because a stack that passes unit-by-unit on a profile
    and has never carried a complete election on it has not been shown to
    work on it.

    It then breaks the record in the way that matters and checks the
    verifier says so, rather than stopping at the green path.
    """
    import dataclasses

    from epd2_voting_service.reference.api import ReferenceApi
    from epd2_voting_service.reference.testing.fixtures import threshold_fixture
    from epd2_voting_service.reference.testing.scenarios import close_and_build, make_ballot
    from epd2_voting_service.reference.verification.results import VerificationResultCode

    bundle = threshold_fixture(params=target, seed=b"crypto1-record")
    fixture = bundle.fixture
    assert is_target_profile(fixture.params.parameter_set_id)

    api = ReferenceApi(store=fixture.store, runtime=fixture.runtime, board=fixture.board)
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"crypto1-record-ballot")
    api.submit_cast_ballot(fixture.capabilities[0], envelope, "idem-crypto1")

    closed = close_and_build(
        fixture,
        [envelope],
        [],
        seed=b"crypto1-close",
        ceremony=bundle.ceremony,
        secrets=bundle.secrets,
    )
    assert closed.record.params.parameter_set_id == TARGET_PROFILE_ID
    assert closed.record.ceremony is not None
    assert api.run_verifier(closed.record).code is VerificationResultCode.VERIFIED

    # Dropping below the quorum on the real parameters must fail exactly as
    # it does on the fast profile — the group size is not what enforces it.
    short = dataclasses.replace(
        closed.record,
        threshold_shares=closed.record.threshold_shares[:2],
    )
    assert api.run_verifier(short).code is VerificationResultCode.GUARDIAN_QUORUM_MISMATCH


def test_the_test_profile_is_not_the_target(target: ParameterSet) -> None:
    """Guards against the two ever being conflated in a later edit."""
    assert small_params().p != target.p
    assert small_params().parameter_set_id != TARGET_PROFILE_ID
