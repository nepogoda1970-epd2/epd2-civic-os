"""The vetted signature provider must be a *declared, locked* dependency.

PACK-16D replaced a hand-written Ed25519 with the `cryptography` library.
That fix is only complete if the dependency is declared where the package
that imports it lives, **and** locked so a reproducible install actually
installs it.

Both halves are now done. `uv.lock` was regenerated on a network-enabled
host and `cryptography` resolves inside the `epd2-voting-service` workspace
graph, with a registry source and per-artifact hashes.

While the lock was unobtainable these tests were deliberately written to
pass in both states — a permanently red test trains a reader to ignore red,
and a red suite hides the next real regression. **That accommodation is
gone.** A missing lock entry is now a failure, and the tests additionally
refuse the two states that would quietly re-open the gap: a lock entry that
looks typed rather than resolved, and an outstanding-lock notice left behind
to rot after the lock caught up.

`uv.lock` is TOML, so it is parsed rather than grepped: a string search
would match the package name inside another package's dependency list and
report a lock entry that does not exist.
"""

from __future__ import annotations

import pathlib
import re
import tomllib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
VOTING_PYPROJECT = ROOT / "services/voting-service/pyproject.toml"
UV_LOCK = ROOT / "uv.lock"
OBLIGATION_DOC = ROOT / "docs/packs/PACK-16/PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md"
RESOLVED_DOC = ROOT / "docs/packs/PACK-16/PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md"
PROVIDER_MODULE = (
    ROOT / "services/voting-service/src/epd2_voting_service/reference/crypto/signature_provider.py"
)

PROVIDER_PACKAGE = "cryptography"
CONSUMING_PACKAGE = "epd2-voting-service"
#: Everything the provider needs, so a partial lock entry is as detectable
#: as a missing one.
EXPECTED_TRANSITIVES = ("cffi", "pycparser")


def _lock() -> dict[str, Any]:
    with UV_LOCK.open("rb") as handle:
        return tomllib.load(handle)


def _locked_package(name: str) -> dict[str, Any] | None:
    for package in _lock().get("package", []):
        if package.get("name") == name:
            return package
    return None


def _declared_specifier() -> str:
    with VOTING_PYPROJECT.open("rb") as handle:
        manifest = tomllib.load(handle)
    for requirement in manifest["project"]["dependencies"]:
        name = re.split(r"[<>=!~\[]", requirement, maxsplit=1)[0].strip()
        if name == PROVIDER_PACKAGE:
            return str(requirement)
    raise AssertionError(
        f"{PROVIDER_PACKAGE} is imported by the reference package but is not "
        f"declared in {VOTING_PYPROJECT.relative_to(ROOT)}"
    )


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version)[:3])


def _satisfies(version: str, specifier: str) -> bool:
    """Does `version` satisfy every clause of `specifier`?

    Deliberately small: this repository pins with `>=` and `<` only, and a
    full PEP 440 implementation here would be a second thing to get wrong.
    An unrecognised operator fails rather than being skipped.
    """
    body = specifier.split(PROVIDER_PACKAGE, 1)[1]
    actual = _version_tuple(version)
    for raw_clause in body.split(","):
        clause = raw_clause.strip()
        if not clause:
            continue
        match = re.fullmatch(r"(>=|<=|==|<|>|!=)\s*([\d.]+)", clause)
        assert match is not None, f"unrecognised version clause {clause!r}"
        operator, bound_text = match.groups()
        bound = _version_tuple(bound_text)
        ok = {
            ">=": actual >= bound,
            "<=": actual <= bound,
            "==": actual == bound,
            "<": actual < bound,
            ">": actual > bound,
            "!=": actual != bound,
        }[operator]
        if not ok:
            return False
    return True


def _artifacts(package: dict[str, Any]) -> list[dict[str, Any]]:
    return list(package.get("wheels", [])) + ([package["sdist"]] if "sdist" in package else [])


# -- declaration ---------------------------------------------------------


def test_cryptography_declared_in_manifest() -> None:
    """`epd2-voting-service` imports it, so `epd2-voting-service` declares it.

    Declaring it at the workspace root instead would make the service
    installable without its own hard requirement — the failure mode that
    produces an ImportError in somebody else's deployment.
    """
    specifier = _declared_specifier()
    assert ">=" in specifier, "the provider must carry a lower bound"
    assert "<" in specifier, "the provider must exclude the next major version"


# -- the lock ------------------------------------------------------------


def test_cryptography_present_in_uv_lock() -> None:
    """The lock resolves the provider, with hashes, from a registry."""
    package = _locked_package(PROVIDER_PACKAGE)
    assert package is not None, (
        f"{PROVIDER_PACKAGE} is declared but absent from uv.lock; run `uv lock`"
    )
    assert package.get("version"), "a lock entry with no version is not a lock entry"
    source = package.get("source", {})
    assert "registry" in source, (
        "no registry source: the entry looks hand-written, which the dependency "
        "policy forbids outright"
    )
    artifacts = _artifacts(package)
    assert artifacts, "no sdist and no wheels: nothing to verify on install"
    assert all("hash" in artifact for artifact in artifacts), (
        "an artifact without a hash defeats the point of locking"
    )
    for transitive in EXPECTED_TRANSITIVES:
        entry = _locked_package(transitive)
        assert entry is not None, (
            f"{PROVIDER_PACKAGE} is locked but its transitive {transitive!r} is not"
        )
        assert all("hash" in artifact for artifact in _artifacts(entry)), (
            f"{transitive!r} is locked without artifact hashes"
        )


def test_locked_cryptography_version_matches_manifest_range() -> None:
    """A lock that resolves outside the declared range is worse than none."""
    package = _locked_package(PROVIDER_PACKAGE)
    assert package is not None
    specifier = _declared_specifier()
    version = str(package["version"])
    assert _satisfies(version, specifier), (
        f"uv.lock resolved {PROVIDER_PACKAGE}=={version}, which does not satisfy "
        f"the declared {specifier!r}"
    )


def test_cryptography_is_in_the_voting_service_graph() -> None:
    """Locked *and reachable from the package that imports it*.

    A lock entry alone proves only that the resolver saw the name somewhere.
    What matters is that `epd2-voting-service` depends on it, so installing
    that service installs the provider. A stray root-level entry would pass
    a presence check while leaving the service importing a package it never
    pulls in.
    """
    service = _locked_package(CONSUMING_PACKAGE)
    assert service is not None, f"{CONSUMING_PACKAGE} is missing from uv.lock"
    dependencies = [entry["name"] for entry in service.get("dependencies", [])]
    assert PROVIDER_PACKAGE in dependencies, (
        f"{PROVIDER_PACKAGE} is locked but is not a dependency of {CONSUMING_PACKAGE}"
    )
    requires = service.get("metadata", {}).get("requires-dist", [])
    declared = [entry for entry in requires if entry.get("name") == PROVIDER_PACKAGE]
    assert declared, f"{PROVIDER_PACKAGE} is absent from {CONSUMING_PACKAGE}'s requires-dist"
    expected = _declared_specifier().removeprefix(PROVIDER_PACKAGE)
    assert declared[0].get("specifier") == expected, (
        "the lock's recorded specifier disagrees with the manifest"
    )


def test_vetted_provider_imports_and_matches_the_lock() -> None:
    """The provider imports, signs, and the running version is the locked one.

    Version equality is the part that earns its keep: it ties the code being
    exercised to the resolution recorded in `uv.lock`, so a green suite run
    against some other build of the library cannot be mistaken for evidence
    about the locked one.
    """
    import cryptography

    from epd2_voting_service.reference.crypto.signature_provider import (
        PROVIDER,
        CryptographyEd25519Provider,
    )

    assert isinstance(PROVIDER, CryptographyEd25519Provider)
    assert PROVIDER.backend.startswith("cryptography")

    package = _locked_package(PROVIDER_PACKAGE)
    assert package is not None
    assert cryptography.__version__ == str(package["version"]), (
        f"the imported {PROVIDER_PACKAGE} is {cryptography.__version__} but uv.lock "
        f"resolves {package['version']}"
    )

    # A real signature, so this is not merely an import check.
    secret = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    _private, public = PROVIDER.generate_test_keypair(secret)
    assert public.hex() == "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    signature = PROVIDER.sign_checkpoint(secret, b"")
    assert PROVIDER.verify_checkpoint(public, b"", signature)


def test_no_custom_ed25519_fallback() -> None:
    """No fallback to a hand-written implementation exists, anywhere.

    The provider module must import the library at module scope and raise
    if it is absent. A `try: import cryptography / except: use our own`
    would silently reinstate exactly what an audit removed, on whichever
    machine happened to lack the dependency.
    """
    reference = ROOT / "services/voting-service/src/epd2_voting_service/reference"
    assert not (reference / "crypto/ed25519.py").exists(), (
        "the hand-written Ed25519 module is back; an audit removed it for a reason"
    )

    source = PROVIDER_MODULE.read_text(encoding="utf-8")
    assert "raise SignatureProviderUnavailableError" in source, (
        "a missing provider must raise, not degrade"
    )
    for banned in ("_recover_x", "_decompress", "def _add(", "def _mul(", "edwards25519"):
        assert banned not in source, f"curve arithmetic is back in the provider: {banned!r}"


# -- the gap must not outlive its cause ---------------------------------


def test_outstanding_lock_notice_did_not_outlive_the_lock() -> None:
    """The obligation is discharged, so its notice must be gone.

    A to-do that outlives its cause is how a repository accumulates lies
    about itself, and this one would be a particularly bad lie: a reader who
    finds "lock regeneration outstanding" next to a regenerated lock cannot
    tell which of the two is stale.
    """
    text = OBLIGATION_DOC.read_text(encoding="utf-8")
    assert "LOCK REGENERATION OUTSTANDING" not in text, (
        "uv.lock now contains the provider, so the outstanding-lock notice in the "
        "dependency assessment is stale and must be removed"
    )


def test_blocked_evidence_is_marked_resolved() -> None:
    """The blocked-evidence record survives, but only as history.

    It is kept rather than deleted because the transcripts are the reason a
    reader can tell an environmental blocker from an excuse. It must not
    read as a live blocker, so the resolution is asserted before the
    evidence and the active phrasing is asserted absent.
    """
    text = RESOLVED_DOC.read_text(encoding="utf-8")
    assert "RESOLVED" in text.split("\n## ", 1)[0], (
        "the environment-blocked record must announce its resolution before its evidence"
    )

    # The old blocked statuses may still be *quoted*, but only under the
    # heading that marks them as history. What is forbidden is one of them
    # standing as a live claim about the repository, so the check is scoped
    # to the part of the document that speaks in the present tense.
    marker = "## HISTORICAL FINDING"
    assert marker in text, (
        "the superseded transcripts must sit under an explicit historical heading, "
        "otherwise a reader cannot tell which half describes the current repository"
    )
    active = text.split(marker, 1)[0]
    for stale in (
        "PACK-16D remains environment blocked",
        "FROZEN CLEAN INSTALL: NOT EXECUTED",
        "IMMUTABLE UPSTREAM IMPLEMENTATION PROVENANCE: PARTIALLY SATISFIED",
        "BLOCKED BY ENVIRONMENT",
    ):
        assert stale not in active, f"stale active wording survives in the record: {stale!r}"


def test_uv_lock_was_not_hand_edited_to_fake_the_provider() -> None:
    """A lock entry must look resolved, not typed.

    Covered structurally by `test_cryptography_present_in_uv_lock`; kept
    under its own name because "was the lock hand-edited" is the question a
    reviewer will actually ask, and it deserves to be greppable.
    """
    package = _locked_package(PROVIDER_PACKAGE)
    assert package is not None
    assert "registry" in package.get("source", {})
    artifacts = _artifacts(package)
    assert artifacts and all("hash" in artifact for artifact in artifacts)
    assert all(str(artifact.get("hash", "")).startswith("sha256:") for artifact in artifacts), (
        "artifact hashes are not sha256-prefixed, which no resolver would produce"
    )
