# PACK-16D — Language and Dependency Assessment

**Round:** PACK-16D — Network-Enabled Finalization: Lockfile Regeneration,
Immutable ElectionGuard Provenance and Final Acceptance Alignment.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Language: Python, `>=3.12`

| ID      | Rule                                                                                                                                                                                         |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LD-01` | **The reference implementation is written in Python and targets `>=3.12`, which is the repository's existing pin.** No new language, runtime or language version is introduced by this round |

The pin was not chosen for this round; it was inherited and matched.
Verified in the repository:

```text
pyproject.toml                          requires-python = ">=3.12"
services/voting-service/pyproject.toml  requires-python = ">=3.12"
pyproject.toml  [tool.mypy]             python_version = "3.12"
pyproject.toml  [tool.uv]               package = false
pyproject.toml  [tool.uv.workspace]     22 members
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LD-02` | **Matching the existing pin was preferred over choosing a language better suited to cryptography.** A second language would mean a second toolchain, a second lint and type configuration, a second CI path and a second body of reviewer expertise — for a package whose purpose is to be _read_. The cost of that choice is stated in `LD-15`: Python cannot give the constant-time properties production cryptography needs, and this round does not pretend otherwise |
| `LD-03` | The package uses no syntax or standard-library behaviour newer than the pin, so it type-checks under the repository's existing `mypy` configuration in the group that covers `services/voting-service` (69 source files) with `Success: no issues found`                                                                                                                                                                                                                  |

---

## 2. Dependencies: exactly one, added deliberately

**This section reverses the previous round's headline claim, and the reversal
is the point.** PACK-16D previously added no dependency at all, and treated
that as the strongest possible form of compliance. It was not. The way that
claim was kept true was by implementing Ed25519 — Edwards-curve point
arithmetic, scalar multiplication, private-key expansion, signing and
verification — inside this repository. An independent audit failed it, and
was right to: "we added no dependency" is worthless if the reason is that we
wrote the cryptographic primitive ourselves.

| ID       | Rule                                                                                                                                                                                                                                                                            |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LD-04`  | **PACK-16D adds exactly one dependency: `cryptography`, for Ed25519.** It is a runtime dependency of `epd2-voting-service`, declared in that package's own `pyproject.toml`. Everything else the reference implementation uses remains the Python standard library or a builtin |
| `LD-04a` | **Zero dependencies was the wrong target.** The right target is _no cryptographic primitive implemented here_. Those two goals pointed in opposite directions, the previous round chose the first, and §2.1 records what that cost                                              |

Otherwise measurable, not asserted. Parsing all **45** modules under
`reference/` — **7 392 lines** of Python — and collecting every non-`epd2`
import yields **15 standard library modules and exactly one third-party
import**, in exactly one module — `crypto/signature_provider.py`. A
structural test (`test_handwritten_ed25519_not_imported`) fails if any other
module in `reference/` imports `cryptography` at all:

| Standard library module | What it supplies                                                                                                                                                                     | Where                                                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `hashlib`               | SHA-256, the digest primitive under the hash profile; the profile-artefact self-digest; stretching a short fixture string into a 32-byte test key                                    | `crypto/hashing.py`, `crypto/parameters.py`, `crypto/randomness.py`, `casting/idempotency.py`, `publication/bulletin_board.py` |
| `hmac`                  | HMAC-SHA-256 — `HASH_PROFILE`                                                                                                                                                        | `crypto/hashing.py` — and nowhere else, since checkpoints are no longer HMAC-signed                                            |
| `secrets`               | The OS CSPRNG behind `ProductionRandomSource`                                                                                                                                        | `crypto/randomness.py` — and nowhere else                                                                                      |
| `unicodedata`           | NFC normalisation, so two Unicode spellings of one string encode identically                                                                                                         | `crypto/encoding.py`                                                                                                           |
| `threading`             | The `RLock` that is the reference store's transaction boundary                                                                                                                       | `casting/store.py`                                                                                                             |
| `copy`                  | `deepcopy` of the outbox rows in the transaction snapshot                                                                                                                            | `casting/store.py`                                                                                                             |
| `contextlib`            | `contextmanager` for `transaction()` and the fault-injection helper                                                                                                                  | `casting/store.py`, `testing/faults.py`                                                                                        |
| `dataclasses`           | Every artefact and record type; frozen and slotted where the value is immutable                                                                                                      | 28 modules                                                                                                                     |
| `enum`                  | `StrEnum` for every closed vocabulary — domain labels, entry types, leaf classes, result codes, fault points, guardian reason codes, checkpoint signature outcomes, evidence classes | 12 modules                                                                                                                     |
| `collections.abc`       | `Sequence`, `Iterator` in signatures                                                                                                                                                 | 7 modules                                                                                                                      |
| `typing`                | `Protocol`, `runtime_checkable`, `Final`                                                                                                                                             | `hooks.py`, `crypto/randomness.py`, `crypto/parameters.py`                                                                     |
| `pathlib`               | Reading the profile artefacts under `crypto/profiles/`                                                                                                                               | `crypto/parameters.py`                                                                                                         |
| `os`                    | Reading the test-profile environment marker                                                                                                                                          | `crypto/randomness.py`, `testing/fixtures.py`                                                                                  |
| `re`                    | The reason-code shape check in the logging allow-list, and hex-shape checking on profile constants                                                                                   | `logging_boundary.py`, `crypto/parameters.py`                                                                                  |
| `json`                  | Serialising the test-vector catalogue and the conformance-evidence catalogue; reading the `EPD2-CRYPTO-1` profile artefact                                                           | `testing/vectors.py`, `testing/conformance.py`, `crypto/parameters.py`                                                         |

Two builtins carry the arithmetic and deserve naming, because they are
where a production implementation will diverge:

| Builtin        | What it supplies                                                                                                                                    | Where                                                           |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `int`          | Arbitrary-precision integers — every group element and scalar is a Python `int`, so there is no bignum library and no width to get wrong            | throughout `crypto/`                                            |
| `pow(a, b, m)` | Modular exponentiation — every ElGamal encryption, every subgroup check, every proof equation, and the Miller–Rabin rounds in `is_probable_prime()` | `crypto/elgamal.py`, `crypto/parameters.py`, `crypto/proofs.py` |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `LD-05` | **One cryptographic library was added, for the one primitive the standard library does not supply.** The protocol needs a hash, an HMAC, a CSPRNG, modular exponentiation over big integers and a digital signature. The standard library supplies the first four honestly — they are compositions of primitives it exposes. It does **not** supply Ed25519, and the gap between "we can build it from `hashlib` and `int`" and "we should" is exactly where the previous round went wrong |
| `LD-06` | **`secrets` is imported in exactly one module.** Randomness enters the system through `crypto/randomness.py` and through no other door, which is what makes the two-guard test-source restriction enforceable                                                                                                                                                                                                                                                                              |

### 2.1 The provider: `cryptography`, assessed

| ID      | Field                                    | Value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LD-19` | Package name                             | `cryptography`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `LD-20` | Declared constraint                      | `cryptography>=46.0.7,<47` in `services/voting-service/pyproject.toml`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `LD-21` | Version this round ran against           | **46.0.7**, linked against OpenSSL **3.5.6 (7 April 2026)**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `LD-22` | Upstream                                 | Python Cryptographic Authority — `https://github.com/pyca/cryptography`, `https://cryptography.io/`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `LD-23` | Licence                                  | Dual Apache-2.0 / BSD-3-Clause, at the user's option                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `LD-24` | Maintenance status                       | Actively maintained; the de facto standard cryptographic library for Python, depended on by the wider Python packaging and TLS ecosystem. Frequent releases, public issue tracker, published changelog                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `LD-25` | Security update model                    | Public security advisories through GitHub Security Advisories and the PyPA ecosystem; CVEs issued against both the Python layer and the vendored/linked OpenSSL. The `<47` ceiling means a major-version security fix requires a deliberate, reviewed bump rather than arriving silently                                                                                                                                                                                                                                                                                                                                                                                                    |
| `LD-26` | Purpose here                             | Ed25519 signature generation and verification for bulletin-board checkpoints. **Nothing else.** No X.509, no TLS, no symmetric primitives, no KDF                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `LD-27` | API used                                 | `Ed25519PrivateKey.from_private_bytes`, `.public_key()`, `.sign()`; `Ed25519PublicKey.from_public_bytes`, `.verify()`, `.public_bytes(Raw, Raw)`. Six calls, all in `crypto/signature_provider.py`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `LD-28` | Native backend involved                  | **Yes.** `cryptography` links a Rust binding layer over OpenSSL's libcrypto. This is a compiled artefact, not pure Python, and the wheel is platform-specific. That is a real supply-chain consideration and is not minimised here                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `LD-29` | Constant-time behaviour claimed          | **Not by EPD².** OpenSSL implements Ed25519 with side-channel resistance as a design goal, and that is a materially better position than the previous hand-written implementation — but EPD² has measured nothing, and `OD-P16D-05` stays open. A library's own design goals are not this repository's evidence                                                                                                                                                                                                                                                                                                                                                                             |
| `LD-30` | Known limitations                        | A compiled native dependency widens the build and supply-chain surface; the wheel must be available for the deployment platform; a CVE in libcrypto becomes an EPD² concern. Against that: the alternative was a from-scratch elliptic-curve implementation maintained by nobody                                                                                                                                                                                                                                                                                                                                                                                                            |
| `LD-31` | Why the standard library is insufficient | Python's standard library has **no** asymmetric signature primitive. `hashlib` and builtin `int` are enough to _build_ Ed25519 — the previous round proved that, and the result agreed with OpenSSL on every vector it was given — but agreement on the vectors an author thought to write is not the property that matters for a curve implementation. What matters is the vulnerability class the author did not think of: a missing subgroup check, a branch that leaks a key bit, a non-canonical encoding accepted on an input nobody tried. Those are found by years of adversarial attention on one widely deployed implementation, and cannot be found by the author of a fresh one |

**The honest summary, in the words the correction requires:**

```text
The vetted provider materially reduces custom cryptographic
implementation risk.

It does not by itself establish production side-channel assurance,
certification or complete BSI conformity.
```

### 2.2 What was removed, and the absence of a fallback

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `LD-32` | **`crypto/ed25519.py` is deleted, not deprecated and not relocated.** The audit's finding was `CHECKPOINT SIGNATURE PRIMITIVE POLICY: FAIL — HANDWRITTEN ED25519`. A file kept "for reference" in a directory excluded from packaging would still be a from-scratch curve implementation in the repository, one import away from being active again                                                                                                                                                                                                          |
| `LD-33` | **There is no fallback, and the absence is enforced rather than intended.** `crypto/signature_provider.py` imports `cryptography` at module scope and raises `SignatureProviderUnavailableError` if it is missing. A `try: import cryptography / except: use our own` would silently reinstate the removed code on whichever machine lacked the dependency — and that machine is the one you would least want running hand-rolled cryptography                                                                                                               |
| `LD-34` | **Both properties are asserted by test, not by review.** `test_handwritten_ed25519_not_imported` parses every module under `reference/` with `ast` and fails on any import of a non-`cryptography` `ed25519` module, any import of `cryptography` outside the provider, and any function named for curve arithmetic. `test_missing_provider_fails_closed` runs a subprocess with the library blocked and asserts the import raises — with a **control run** first, so the test cannot pass merely because the subprocess could never have imported it anyway |
| `LD-35` | **The provider decides validity, never trust.** It answers "is this signature valid for this key over these bytes" and has no opinion on whose key it is. Signer authorisation stays in `SignerRegistry` and the election context. A provider that also decided trust would be two mechanisms wearing one name                                                                                                                                                                                                                                               |

### 2.3 Test oracles are still not dependencies

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LD-36` | **The OpenSSL _command-line tool_ is an out-of-process oracle.** `tests/reference/crossimpl/openssl_cli_ed25519_oracle.py` shells out to the `openssl` binary — a separately built, separately versioned artefact (OpenSSL 3.0.13 here) — and speaks to it only through files and exit codes. It imports no cryptographic Python library at all: a raw public key is wrapped in its twelve fixed DER prefix bytes by hand                                                                                                                                     |
| `LD-37` | **That oracle is weaker than it was, and the weakening is stated.** When the primitive was hand-written, comparing it against OpenSSL was strong evidence. Now that the _provider_ is OpenSSL, a CLI comparison shares an upstream with the thing it checks, so a defect present in both builds would be invisible. The evidence that does not share a lineage is the **RFC 8032 §7.1 published vectors**, checked directly against the provider — and those are now the primary conformance evidence for the signature scheme, with the CLI as corroboration |
| `LD-38` | **Node.js is used only by an out-of-process oracle.** `tests/reference/crossimpl/independent_verifier.mjs` re-derives the canonical encoding from the written grammar, implements its own square-and-multiply modular exponentiation, and imports only `node:` builtins. **No npm package is involved**, `package-lock.json` is untouched, and the entire npm toolchain remained unexecuted this round                                                                                                                                                        |
| `LD-39` | **An oracle that must be independent cannot be a dependency.** Cross-implementation evidence is worth something only when the comparing implementation shares no code with the compared one. Vendoring either oracle into the dependency graph would weaken exactly the property it exists to establish                                                                                                                                                                                                                                                       |

---

## 3. The prohibited dependency shapes

The repository's dependency policy prohibits four shapes. The previous round
answered "not applicable" to all four, because it had added nothing. That
answer is no longer available, and `LD-12` said as much in advance: adding a
cryptographic dependency **re-opens all four assessments**. They are run
properly below.

| ID      | Prohibited shape                                                                                                 | Assessment for `cryptography`                                                                                                                                                                                                                                                                                                                                                                                 |
| ------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LD-07` | **Unversioned Git source** — resolved from a branch or a moving reference rather than a released, pinned version | **Not present.** Declared as `cryptography>=46.0.7,<47`, a released version range from the public index. No Git source, no URL dependency, no branch reference. The released version range is now resolved and hash-pinned in `uv.lock` as `cryptography 46.0.7`; §4 records the regeneration and the checks run against it                                                                                   |
| `LD-08` | **Runtime download** — code fetched during execution rather than resolved at build time                          | **Not present.** `cryptography` is resolved at install time like any other package. Nothing in `reference/` opens a network connection; the only file reads are the three profile artefacts shipped inside the package under `crypto/profiles/`                                                                                                                                                               |
| `LD-09` | **Browser CDN delivery** — a script served to a client from a third-party origin                                 | **Not applicable.** `cryptography` is server-side Python. This round ships no browser-delivered artefact at all, and the Node and frontend toolchain was not executed (`npm ci` returns HTTP 403 here)                                                                                                                                                                                                        |
| `LD-10` | **Proprietary opacity** — a dependency whose source cannot be read and reviewed                                  | **Not present, with a caveat.** `cryptography` is open source under Apache-2.0/BSD-3-Clause, as is the OpenSSL it links. The caveat is `LD-28`: a compiled native artefact is reviewable in principle and is not read line-by-line by this repository's reviewers in practice. That is true of the Python runtime itself, and it is the trade the policy exists to make deliberately rather than accidentally |

| ID       | Rule                                                                                                                                                                                                                                                                                                                                                                           |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `LD-11`  | **This is a real assessment, not the previous round's tautology.** Last round's compliance came from having created no exposure; it read as strength and was concealing a worse one. This round has an exposure, names it, and states what would change the answer: abandonment of `cryptography`, a licence change, or a security-response record that stopped being credible |
| `LD-12`  | **The assessment is per-round and does not transfer.** A future round adding a second cryptographic dependency — for the constant-time bignum path of `LD-15`, most plausibly — re-opens all four again                                                                                                                                                                        |
| `LD-12a` | **One dependency is the ceiling this round claims, not a direction of travel.** The provider covers signatures. It is deliberately not used for hashing, randomness, or the group arithmetic, all of which remain standard library, because widening its footprint would trade a reviewable implementation for an unreviewed one without an audit finding asking for it        |

---

## 4. Lock-file status

| File                                     | Status this round                                                                                                                                                       |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `services/voting-service/pyproject.toml` | **Modified.** One dependency added: `cryptography>=46.0.7,<47`                                                                                                          |
| `pyproject.toml` (root)                  | **Unchanged.** The provider belongs to the package that imports it, not to the workspace root                                                                           |
| `uv.lock`                                | **REGENERATED** by `uv lock` on a network-enabled host. `1a1e5a72…d543` → `b2d07754…8066`; 149 lines added, 0 removed, no existing package's version changed. See below |
| `package-lock.json`                      | **Unchanged.** No Node dependency exists; the Node oracle uses only builtins                                                                                            |

### 4.1 Lock regenerated and verified

```text
DEPENDENCY LOCK:
REGENERATED

FROZEN CLEAN INSTALL:
EXECUTED ON A NETWORK-ENABLED HOST
```

For two rounds this section carried an outstanding-lock notice, because the
provider was declared in `pyproject.toml` and absent from `uv.lock`, and the
build environment's egress allowlist refused `pypi.org`. The notice is gone
because the obligation is discharged — a to-do that outlives its cause is how a
repository accumulates lies about itself, and
`test_outstanding_lock_notice_did_not_outlive_the_lock` fails if that wording
ever reappears next to a regenerated lock.

```console
$ uv lock
$ rm -rf .venv
$ uv sync --all-groups --frozen
Checked 61 packages
```

```text
old uv.lock SHA-256   1a1e5a72b67b92a53b189e6eb9c9f4305f236a0aa76f7d55887f24ad2a76d543
new uv.lock SHA-256   b2d0775458d3b6e81d321724530c7a473584fb2b3d9d231d220d8e9dcdfe8066
declared range        cryptography>=46.0.7,<47
resolved version      cryptography 46.0.7
transitives           cffi 2.1.0 (binding layer to OpenSSL), pycparser 3.0 (cffi's C parser)
delta                 149 lines added, 0 removed, 0 existing versions changed
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `LD-13` | **Neither lock file was hand-edited, and neither may ever be.** This is why the gap was left open for two rounds rather than papered over: a `uv.lock` entry requires a registry source and distribution hashes for artefacts that were never downloaded, and typing plausible hashes would produce a file that looks resolved and is not. The entry now present was produced by the resolver                                                                                                                                                                      |
| `LD-40` | **Why it could not be regenerated here.** `uv lock` re-resolves the _entire_ workspace against an index. The build environment's egress proxy returned **HTTP 403** for `pypi.org` and `files.pythonhosted.org`, and uv's local cache contained none of the repository's other dependencies — `uv lock --offline` failed on `hypothesis` before ever reaching `cryptography`. Recorded as a `HISTORICAL FINDING` in `PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md`                                                                                                     |
| `LD-41` | **The delta is purely additive, which is the shape a single new dependency should produce.** Three entries appeared and nothing else moved: no existing package changed version, no entry was removed, `requires-python` and the lock revision are unchanged. A regeneration that had churned unrelated versions would deserve its own scrutiny, and this one did not                                                                                                                                                                                              |
| `LD-42` | **Each new entry is explained rather than merely listed.** `cryptography` is the vetted Ed25519 provider; `cffi` is how it binds to OpenSSL; `pycparser` is `cffi`'s own C parser. There is no fourth                                                                                                                                                                                                                                                                                                                                                              |
| `LD-43` | **The requirement is held open by tests, not by this paragraph.** `tests/repository/test_pack16d_signature_dependency.py` now fails if the provider is missing from the lock, if a lock entry appears without a registry source and `sha256:`-prefixed hashes — the shape a hand-edit would produce — if the resolved version falls outside the declared range, or if `cryptography` is locked but is not a dependency of `epd2-voting-service`. It also fails if this document's outstanding-lock notice ever returns                                             |
| `LD-44` | **The lock is parsed, not grepped.** `uv.lock` is TOML and the tests read it with `tomllib`. A string search for `cryptography` matches the name inside _other_ packages' dependency lists and would report a lock entry that does not exist — the exact false pass this row is here to prevent                                                                                                                                                                                                                                                                    |
| `LD-45` | **The version check is real, not decorative.** `test_locked_cryptography_version_matches_manifest_range` compares the resolved version against every clause of the declared specifier. It was verified to accept `46.0.7` and reject both `45.0.0` and `47.0.0`, so it is not a tautology                                                                                                                                                                                                                                                                          |
| `LD-46` | **Locked in the right graph, not merely present.** A lock entry alone proves only that the resolver saw the name somewhere. `test_cryptography_is_in_the_voting_service_graph` asserts that `epd2-voting-service` depends on it and that the manifest specifier is echoed in `requires-dist`, so installing the service installs the provider                                                                                                                                                                                                                      |
| `LD-47` | **The resolved version is now a property of the repository, and the distinction that made this row necessary still holds.** The declared range is `>=46.0.7,<47` and the resolution is `46.0.7`. Separately, the running library's version is asserted equal to the locked one, which ties the code the suite exercises to the recorded resolution — but `uv sync --all-groups --frozen` was executed on the network-enabled host and not in the build session, so "the tests are green" and "the frozen install passes" remain two claims and are recorded as two |

### 4.2 What this means for an auditor

An auditor should treat the signature-provider change as **implemented in code
and locked in packaging**. The code half is testable in any environment and was
tested: 44 checkpoint-signature tests pass against the vetted provider,
including the RFC 8032 published vectors and an independent OpenSSL CLI
comparison. The packaging half is now resolved in `uv.lock`, with the checks in
§4.1 run against the lock's parsed contents rather than its text.

One boundary is worth an auditor's attention because it is the kind of thing a
summary tends to swallow: the `uv sync --all-groups --frozen` run happened on
the network-enabled host that regenerated the lock, not in the session that
produced this candidate, which still has no package index. What that session can
and does show is that the lock's contents are well-formed and in the right
dependency graph, and that the `cryptography` build the test suite imports is
version-identical to the locked resolution. What it cannot show first-hand is
the install itself.

---

## 5. Declared development dependencies that could not be installed

Two dependencies are declared in the repository's dev group and were not
usable this round. Both are reported here rather than in a footnote,
because each weakens a specific piece of evidence.

| Declared dependency | Status                              | What it costs                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `hypothesis`        | **Not installable** (PyPI HTTP 403) | The property tests are deterministic seeded loops over a `DeterministicTestRandomSource`, 40 cases each. They cover the property space but **do not shrink counterexamples and do not search adversarially**. `test_property.py` states this in its module docstring, and a test asserts that `import hypothesis` still fails, so the limitation cannot be quietly dropped. Converting them to real strategies is `OD-P16D-03`, a PACK-17 item |
| `pytest-cov`        | **Not installable** (PyPI HTTP 403) | Line coverage of the reference package was measured with the stdlib `trace` module instead: **90.9 % (3 816 / 4 200 executable lines)**. **Branch coverage was not measured** — no tool for it is available here — and must not be claimed. The `0.0 %` rows for `__init__.py` files and `testing/fixtures.py` are a tracing artefact of modules imported before tracing starts, not untested code                                             |

A related caveat on the toolchain itself: `ruff`, `mypy` and `pytest` were
run from a standalone toolchain rather than through `uv run`, so the
versions used may differ from the pinned ones. Measured: `mypy` **1.20.2**
(matching the pin) and `pytest` 9.x; the repository pins `ruff` 0.15.11.
An auditor with network access must re-run these through `uv run` to
confirm.

Two pieces of software present in this environment are used **only** as
out-of-process test oracles and are not repository dependencies: the
`openssl` **binary** (3.0.13) and a Node.js runtime (v22.22.2). Neither
appears in a lock file and neither is imported by the reference
implementation — see `LD-36` … `LD-39`. An auditor without them cannot run
those cross-implementation checks; the checks **fail loudly** rather than
skipping, so their absence is reported as missing evidence rather than
passing silently.

`cryptography` is a different case and must not be filed alongside them any
more: it is now a **declared runtime dependency** (`LD-04`), present in this
environment at 46.0.7 and reached through `PYTHONPATH` rather than through a
resolved install, because the lock could not be regenerated (§4.1). That is
how every workspace package is reached here — the repository's own
`LOCAL_VERIFICATION.md` records the same arrangement — but it means the
provider's _installation_ is as unverified as the lock is.

---

## 6. The trade-off, stated honestly

| ID       | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LD-15`  | **Python big-integer arithmetic is not constant-time, and `pow(a, b, m)` offers no side-channel guarantee.** Execution time and memory behaviour depend on operand values. A secret exponent — a nonce, a proof witness, a guardian polynomial coefficient, a guardian secret key share — is therefore exposed to a timing or microarchitectural observer with sufficient access to the executing host                                                                                                                                                |
| `LD-16`  | **No constant-time or side-channel property is claimed anywhere in PACK-16D.** `crypto/proofs.py` says so in its own source. Any document, comment, test name or release note that implies otherwise is wrong and must be corrected rather than qualified                                                                                                                                                                                                                                                                                             |
| `LD-16a` | **The signature surface improved and is still not assured.** Ed25519 signing moved from a hand-written, openly non-constant-time implementation to OpenSSL, which pursues side-channel resistance as a design goal. That is a real reduction in risk and it is **not** an assurance: EPD² has measured nothing, and a library's stated goals are not this repository's evidence. `OD-P16D-05` is narrowed in scope, not closed                                                                                                                        |
| `LD-17`  | **A production implementation still needs a constant-time bignum path** for the group arithmetic, the proofs and the guardian secret operations, which remain pure Python. This is recorded as `OD-P16D-05`: a residual risk and a **production blocker**, not a known-issue to be carried indefinitely. It is not mitigated by the reference implementation and cannot be mitigated by any amount of Python. `PACK-16D-SECURITY-AND-SIDE-CHANNEL-LIMITATIONS.md` §4 separates the four surfaces and states which of them the blocker actually blocks |
| `LD-18`  | **Secret material is not zeroized either.** Python cannot reliably zeroize an immutable `int` or `bytes` — the garbage collector may copy the value before any overwrite could take effect. This is stated as an unsolved limitation                                                                                                                                                                                                                                                                                                                  |

The honest summary of §6 is that the language choice in `LD-01` bought
reviewability and cost side-channel resistance. That was the right trade
for a reference implementation whose job is to make a specification
checkable, and it is the wrong trade for production. Both halves of that
sentence are part of the decision.

---

## 7. What this document does not decide

```text
What is in and out of scope this round      → PACK-16D-SCOPE-AND-IMPLEMENTATION-BOUNDARY.md
Layering, placement and dependency direction → PACK-16D-IMPLEMENTATION-ARCHITECTURE.md
Cryptographic module surfaces and rules      → PACK-16D-CRYPTOGRAPHIC-MODULE-MAP.md
Constant-time bignum path                    → OD-P16D-05, PACK-17
Constant-time Ed25519 for the signing side   → OD-P16D-05, PACK-17, see LD-22
Whether either test oracle should ever become a dependency
                                             → no; see LD-25
Hypothesis-based property testing            → OD-P16D-03, PACK-17
Branch coverage tooling                      → PACK-17
Re-running the toolchain through `uv run`    → PACK-17, an environment with network access
Language choice for any production component → out of scope; this round assesses the
                                               reference implementation only
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
