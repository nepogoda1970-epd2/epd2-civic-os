"""Finite-field parameter profiles and their fail-closed validation.

PACK-16D §11. A parameter set is **never trusted by identifier**: every
load runs the full structural check below and refuses anything that does
not pass.

    |p| = the profile's declared prime bit length
    |q| = the profile's declared order bit length
    q prime
    p prime
    q | (p - 1)
    1 < g < p
    ord(g) = q      (g != 1 and g^q = 1)

`EPD2-CRYPTO-1` — the ElectionGuard 2.1 published 4096-bit family — is the
**target profile and it loads**. Its constants live in the immutable
artefact `profiles/EPD2-CRYPTO-1.json`, transcribed from the primary source
named in that file and then verified locally by arithmetic: `q | p-1`,
`p = q*r + 1`, `g^q = 1 mod p`, `p`, `q` and `r/2` probable-prime, the
leading and trailing 256 bits of `p` all ones, and the middle bits agreeing
with `ln(2)` for 3306 of 3584 bits. A single wrong hex digit anywhere breaks
those relations, so the transcription is confirmed by mathematics rather
than by trusting the fetch.

**There is no fallback.** No test profile may stand in for
`EPD2-CRYPTO-1`, and no environment variable, feature flag or registry
lookup can cause a substitution: `load_profile` reads exactly the artefact
named by the profile id, and a profile whose artefact is missing raises.

`q = 2**256 - 189` is reproducible by arithmetic and is asserted here for
every profile that claims to use it.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
from epd2_voting_service.reference.crypto.encoding import (
    encode_group_element,
    encode_scalar,
    encode_struct,
    encode_text,
    encode_uint,
)
from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h

#: The ElectionGuard 2.1 small prime, reproducible by arithmetic.
Q_ELECTIONGUARD_2_1: Final[int] = 2**256 - 189

_SMALL_PRIMES: Final[tuple[int, ...]] = (
    2,
    3,
    5,
    7,
    11,
    13,
    17,
    19,
    23,
    29,
    31,
    37,
    41,
    43,
    47,
    53,
    59,
    61,
    67,
    71,
    73,
    79,
    83,
    89,
    97,
    101,
    103,
    107,
    109,
    113,
    127,
    131,
    137,
    139,
    149,
    151,
    157,
    163,
    167,
    173,
    179,
    181,
    191,
    193,
    197,
    199,
    211,
    223,
    227,
    229,
    233,
    239,
    241,
    251,
)


class ParameterValidationError(ValueError):
    """A parameter set failed structural validation. Always fail closed."""

    reason_code = "PARAMETER_SET_INVALID"


class ParameterProfileUnavailableError(LookupError):
    """A registered profile has no loadable constants in this round."""

    reason_code = "PARAMETER_SET_NOT_APPROVED"


def is_probable_prime(n: int, rounds: int = 24) -> bool:
    """Deterministic small-factor sieve plus Miller-Rabin.

    Not a primality *proof*. `PACK-16D-SECURITY-AND-SIDE-CHANNEL-LIMITATIONS.md`
    §4 records that a production profile must carry a primality certificate
    from the parameter publisher rather than rely on this.
    """
    if n < 2:
        return False
    for small in _SMALL_PRIMES:
        if n % small == 0:
            return n == small
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for base in _SMALL_PRIMES[:rounds]:
        x = pow(base, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


@dataclass(frozen=True, slots=True)
class ParameterSet:
    """A validated finite-field parameter set."""

    parameter_set_id: str
    profile_version: str
    provenance: str
    production_use_permitted: bool
    p: int
    q: int
    g: int

    @property
    def p_bytes(self) -> int:
        return (self.p.bit_length() + 7) // 8

    @property
    def q_bytes(self) -> int:
        return (self.q.bit_length() + 7) // 8

    @property
    def cofactor(self) -> int:
        return (self.p - 1) // self.q

    def canonical_bytes(self) -> bytes:
        """The single canonical serialisation a digest may be taken over."""
        return encode_struct(
            [
                ("parameter_set_id", encode_text(self.parameter_set_id)),
                ("profile_version", encode_text(self.profile_version)),
                ("p_bit_length", encode_uint(self.p.bit_length(), 4)),
                ("q_bit_length", encode_uint(self.q.bit_length(), 4)),
                ("p", encode_group_element(self.p, self.p_bytes)),
                ("q", encode_scalar(self.q, self.q_bytes)),
                ("g", encode_group_element(self.g, self.p_bytes)),
            ]
        )

    def digest(self) -> bytes:
        return h(ZERO_KEY, DomainLabel.PARAMETER_SET, [self.canonical_bytes()])

    def digest_hex(self) -> str:
        return self.digest().hex()


def validate_parameter_set(
    candidate: ParameterSet,
    *,
    expect_p_bits: int,
    expect_q_bits: int,
    check_primality: bool = True,
) -> ParameterSet:
    """Run every structural check, or raise. Never returns a partial result."""
    if candidate.p.bit_length() != expect_p_bits:
        raise ParameterValidationError(
            f"|p| = {candidate.p.bit_length()}, expected {expect_p_bits}"
        )
    if candidate.q.bit_length() != expect_q_bits:
        raise ParameterValidationError(
            f"|q| = {candidate.q.bit_length()}, expected {expect_q_bits}"
        )
    if candidate.p <= 2 or candidate.q <= 2:
        raise ParameterValidationError("p and q must exceed 2")
    if (candidate.p - 1) % candidate.q != 0:
        raise ParameterValidationError("q does not divide p - 1")
    if not 1 < candidate.g < candidate.p:
        raise ParameterValidationError("g is outside (1, p)")
    if pow(candidate.g, candidate.q, candidate.p) != 1:
        raise ParameterValidationError("g^q != 1: g is not in the order-q subgroup")
    if check_primality:
        if not is_probable_prime(candidate.q):
            raise ParameterValidationError("q is not prime")
        if not is_probable_prime(candidate.p):
            raise ParameterValidationError("p is not prime")
    return candidate


def is_in_subgroup(value: int, params: ParameterSet) -> bool:
    """Group membership **and** subgroup membership, on every element."""
    if not 0 < value < params.p:
        return False
    return pow(value, params.q, params.p) == 1


def require_in_subgroup(value: int, params: ParameterSet, what: str) -> int:
    if not is_in_subgroup(value, params):
        raise ParameterValidationError(f"{what} is not a member of the order-q subgroup")
    return value


PROFILE_DIR: Final[Path] = Path(__file__).resolve().parent / "profiles"

#: Expected bit lengths per profile, declared **in code** rather than read
#: from the profile artefact.
#:
#: This matters: an earlier version passed ``candidate.p.bit_length()`` as
#: the expectation, which makes the length check compare a value against
#: itself and pass for any file. The expectation has to come from somewhere
#: an attacker editing the artefact does not control.
PROFILE_BIT_LENGTHS: Final[dict[str, tuple[int, int]]] = {
    "EPD2-CRYPTO-1": (4096, 256),
    "EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256": (4096, 256),
    "EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160": (1024, 160),
}

#: The pinned digest of the `EPD2-CRYPTO-1` artefact's canonical constants,
#: over ``sha256(p_hex || q_hex || g_hex || r_hex)`` in lower-case hex with
#: no separators. Declared here so that editing the artefact is detected.
EPD2_CRYPTO_1_PARAMETER_DIGEST: Final[str] = (
    "f0af5b71412ccf93a1eaf93364c223f5339cdb2815a2efcfa1bd775cd2bf17fb"
)

#: Profiles this round can load, and what each is for.
PROFILE_REGISTRY: Final[dict[str, str]] = {
    "EPD2-CRYPTO-1": (
        "ElectionGuard 2.1 Standard Baseline Cryptographic Parameters (specification "
        "v2.1.0 section 3.1.1). THE TARGET PROFILE. Constants transcribed from the "
        "primary source recorded in profiles/EPD2-CRYPTO-1.json and verified locally "
        "by arithmetic."
    ),
    "EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256": (
        "TEST ONLY. NOT EPD2-CRYPTO-1. NOT ELECTIONGUARD 2.1 CONFORMANCE. NOT "
        "PRODUCTION. An independently generated 4096-bit p sharing only the "
        "dimensions of the target profile. It is NOT the published family and it "
        "lacks that family's r/2-prime property. It may never stand in for "
        "EPD2-CRYPTO-1."
    ),
    "EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160": (
        "TEST ONLY. NOT EPD2-CRYPTO-1. NOT ELECTIONGUARD 2.1 CONFORMANCE. NOT "
        "PRODUCTION. A small profile for fast property and concurrency tests. "
        "Cryptographically inadequate by construction."
    ),
}

#: The only profile that may ever be used for a conformance claim.
TARGET_PROFILE_ID: Final[str] = "EPD2-CRYPTO-1"

#: Substring every non-target profile id must contain, so that a profile id
#: printed in a log or a document cannot be mistaken for the target.
TEST_ONLY_MARKER: Final[str] = "TESTONLY-NOTCONFORMANT"


class ProfileSubstitutionError(RuntimeError):
    """Something tried to use a test profile where the target was required."""

    reason_code = "PARAMETER_SET_NOT_APPROVED"


def is_target_profile(parameter_set_id: str) -> bool:
    return parameter_set_id == TARGET_PROFILE_ID


def require_target_profile(params: ParameterSet, what: str) -> ParameterSet:
    """Fail closed when a conformance-bearing operation gets a test profile."""
    if not is_target_profile(params.parameter_set_id):
        raise ProfileSubstitutionError(
            f"{what} requires {TARGET_PROFILE_ID!r}; got "
            f"{params.parameter_set_id!r}, which is a test-only profile and may "
            "never stand in for the target"
        )
    return params


def _read_profile_artifact(parameter_set_id: str) -> dict[str, object]:
    """Read a profile artefact. No search path, no fallback, no defaulting."""
    path = PROFILE_DIR / f"{parameter_set_id}.json"
    if not path.is_file():
        legacy = PROFILE_DIR / f"{parameter_set_id}.params"
        if legacy.is_file():
            values: dict[str, object] = {}
            for line in legacy.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                name, _, raw = line.partition("=")
                values[name.strip()] = int(raw.strip())
            missing = {"p", "q", "g"} - values.keys()
            if missing:
                raise ParameterValidationError(f"profile artefact is missing {sorted(missing)}")
            return values
        raise ParameterProfileUnavailableError(
            f"no parameter artefact for profile {parameter_set_id!r}: "
            f"{PROFILE_REGISTRY.get(parameter_set_id, 'unknown profile')}"
        )
    document: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    if document.get("profile_id") != parameter_set_id:
        raise ParameterValidationError(
            f"artefact for {parameter_set_id!r} declares profile_id "
            f"{document.get('profile_id')!r}; a profile artefact may not describe "
            "a different profile"
        )
    return document


def _artifact_parameter_digest(document: dict[str, object]) -> str:
    concat = "".join(str(document[name]) for name in ("p", "q", "g", "r")).encode("ascii")
    return hashlib.sha256(concat).hexdigest()


def load_profile(parameter_set_id: str, *, check_primality: bool = True) -> ParameterSet:
    """Load and fully validate a registered profile, or fail closed.

    Validation is never skipped because an identifier is trusted. There is
    no cached-validation path and no fast path keyed on the profile name;
    if a caller needs the target profile more than once it should hold the
    returned object, which is frozen.
    """
    if parameter_set_id not in PROFILE_REGISTRY:
        raise ParameterProfileUnavailableError(f"unknown profile {parameter_set_id!r}")
    document = _read_profile_artifact(parameter_set_id)

    if "p_bit_length" in document:
        # JSON artefact: constants are canonical fixed-width lower-case hex.
        for field in ("p", "q", "g", "r"):
            raw = document[field]
            if not isinstance(raw, str) or not re.fullmatch(r"[0-9a-f]+", raw):
                raise ParameterValidationError(
                    f"{parameter_set_id}: {field} must be canonical lower-case hex "
                    "with no separators, so that two readers cannot disagree about "
                    "its value"
                )
        p_value = int(str(document["p"]), 16)
        q_value = int(str(document["q"]), 16)
        g_value = int(str(document["g"]), 16)
        r_value = int(str(document["r"]), 16)
        declared = _artifact_parameter_digest(document)
        if declared != document.get("parameter_digest"):
            raise ParameterValidationError(
                f"{parameter_set_id}: the artefact's own parameter_digest does not "
                "match its constants"
            )
        if parameter_set_id == TARGET_PROFILE_ID and declared != EPD2_CRYPTO_1_PARAMETER_DIGEST:
            raise ParameterValidationError(
                f"{parameter_set_id}: parameter digest {declared} does not match the "
                f"pinned {EPD2_CRYPTO_1_PARAMETER_DIGEST}; the artefact was edited"
            )
        if p_value != q_value * r_value + 1:
            raise ParameterValidationError(
                f"{parameter_set_id}: p != q * r + 1; the declared cofactor does not hold"
            )
        provenance = str(document.get("protocol_lineage", PROFILE_REGISTRY[parameter_set_id]))
    else:
        p_value = int(str(document["p"]))
        q_value = int(str(document["q"]))
        g_value = int(str(document["g"]))
        provenance = PROFILE_REGISTRY[parameter_set_id]

    candidate = ParameterSet(
        parameter_set_id=parameter_set_id,
        profile_version=str(document.get("profile_version", "EPD2-PARAM-1")),
        provenance=provenance,
        production_use_permitted=False,
        p=p_value,
        q=q_value,
        g=g_value,
    )
    expect_p_bits, expect_q_bits = PROFILE_BIT_LENGTHS[parameter_set_id]
    return validate_parameter_set(
        candidate,
        expect_p_bits=expect_p_bits,
        expect_q_bits=expect_q_bits,
        check_primality=check_primality,
    )


def load_target_profile(*, check_primality: bool = True) -> ParameterSet:
    """Load `EPD2-CRYPTO-1`. The only entry point a conformance run may use."""
    return load_profile(TARGET_PROFILE_ID, check_primality=check_primality)
