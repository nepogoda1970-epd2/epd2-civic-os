# PACK-16D — Environment-Blocked Evidence — **RESOLVED (HISTORICAL RECORD)**

**Status:** `ENVIRONMENT BLOCKERS RESOLVED ON NETWORK-ENABLED HOST`
**Round:** PACK-16D — Network-Enabled Finalization. A correction of the PACK-16D
reference-implementation candidate, not a new round.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. What this document is now

Two defects raised by an earlier audit could not be closed in the build
environment: `uv.lock` could not be regenerated, and the corroborating
ElectionGuard implementation source could not be commit-pinned. Both were
recorded here as blocked, with verbatim transcripts, rather than worked around.

**Both are now resolved.** The commands were executed on a host with the
required network access and the results are in §1.1 and §2.1. This document is
kept — not deleted — because the original transcripts are what let a reader tell
an environmental blocker from an excuse, and because the resolution is only
meaningful next to the thing it resolved.

| ID | Rule |
| -- | ---- |
| `EB-17` | **Everything under the HISTORICAL FINDING heading is superseded.** It describes the state of a build environment on 2026-08-02. It does not describe the current repository and must not be quoted as if it did |
| `EB-18` | **The record was not rewritten to look better.** The failed transcripts are reproduced unchanged. A resolved blocker whose evidence has been tidied away is indistinguishable from one that was never real |

---

## 1. Defect A — dependency lock — **RESOLVED**

### 1.1 Resolving evidence

Executed on a network-enabled host:

```console
$ uv lock
$ rm -rf .venv
$ uv sync --all-groups --frozen
Checked 61 packages
```

Recorded outcome:

```text
old uv.lock SHA-256   1a1e5a72b67b92a53b189e6eb9c9f4305f236a0aa76f7d55887f24ad2a76d543
new uv.lock SHA-256   b2d0775458d3b6e81d321724530c7a473584fb2b3d9d231d220d8e9dcdfe8066
declared range        cryptography>=46.0.7,<47
resolved version      cryptography 46.0.7
new lock entries      cryptography 46.0.7, cffi 2.1.0, pycparser 3.0
lock diff             149 lines added, 0 removed, 0 existing versions changed
```

| ID | Rule |
| -- | ---- |
| `EB-19` | **One transcription discrepancy is recorded rather than silently corrected.** The finalization brief quoted the new lock digest as `02d0775458…`; the digest computed over the delivered file's actual bytes is `b2d0775458…`. The two differ in the **first hex character only** and agree in the remaining 63, which is not a possible outcome of file corruption — SHA-256 avalanche makes a one-nibble difference from changed bytes about as likely as guessing the digest outright. It is a transcription slip in the brief. The computed value governs, because it is the one anybody can reproduce from the file |
| `EB-20` | **Three entries, and each is explained.** `cryptography` is the vetted Ed25519 provider; `cffi` is its binding layer to OpenSSL; `pycparser` is `cffi`'s own C parser. No fourth package appeared, and no existing package changed version — the lock delta is purely additive |
| `EB-21` | **`Checked 61 packages` against 62 lock entries is expected**, not a discrepancy: the workspace root is a lock entry that is not itself installed as a distribution |

### 1.2 Verification performed in the build session

The lock was **verified, not regenerated blindly**. `uv.lock` is parsed as TOML
rather than searched as text, because a string search matches the package name
inside another package's dependency list and reports an entry that does not
exist. Checks, all green:

```text
cryptography present in uv.lock                      yes
source is a registry (https://pypi.org/simple)       yes
artifact hashes present on all 43 artifacts          yes, all sha256:-prefixed
resolved 46.0.7 satisfies >=46.0.7,<47               yes
cffi 2.1.0 and pycparser 3.0 locked with hashes      yes
cryptography in epd2-voting-service dependencies     yes
requires-dist specifier matches the manifest         yes
existing package versions changed                    none
imported cryptography version == locked version      yes (46.0.7)
```

The last line matters: it ties the code the suite exercises to the resolution
recorded in the lock, so a green run against some other build of the library
cannot be mistaken for evidence about the locked one.

| ID | Rule |
| -- | ---- |
| `EB-22` | **`uv sync --all-groups --frozen` was executed on the network-enabled host, not in the build session.** The build session still has no package index, so it verifies the lock's *contents* and the running library's *version*; it does not re-run the install. The distinction is stated because "the tests are green" and "the frozen install passes" are different claims |

## 2. Defect B — immutable upstream provenance — **RESOLVED**

### 2.1 Resolving evidence

```text
repository        https://github.com/microsoft/electionguard-rust
upstream commit   520651138110a13f777409e96606454df928ceac
commit date       2025-02-02T22:17:21-08:00
source file       src/eg/src/standard_parameters.rs
pinned raw URL    https://raw.githubusercontent.com/microsoft/electionguard-rust/
                  520651138110a13f777409e96606454df928ceac/src/eg/src/standard_parameters.rs
source SHA-256    ad38bfa68d31131a7d721e08d359224b21e967aae4d517534a60a109e10f5770
retrieval date    2026-08-03
```

All six fields are now in `EPD2-CRYPTO-1.json` under `source.corroborating`, and
`unpinned_reason` and `auditor_action` were removed **in the same change** — a
repository that keeps an excuse next to the thing the excuse was for is telling a
reader two incompatible stories. `test_epd2_crypto_1_source_commit_present`
fails if both are ever present at once again.

| ID | Rule |
| -- | ---- |
| `EB-23` | **The digest's verification scope is recorded in the artefact itself.** The value was computed on the network-enabled host. The build session verified internal consistency — 40-character lower-case object id, pinned URL containing that exact commit and that exact path, 64 lower-case hex digest — and re-derived every parameter offline, but it did **not** re-fetch the upstream bytes and does not claim to have. An auditor closes that last gap with one command: `curl -sL <pinned-url> \| sha256sum` |
| `EB-24` | **The pin does not promote the implementation source.** It stays corroborating, `is_normative: false`, and the normative reference remains the ElectionGuard Design Specification v2.1.0 §3.1.1 at a versioned release asset. The tempting misreading after a successful pin is "both are solid now, so either will do" — `test_epd2_crypto_1_normative_and_corroborating_sources_distinct` exists to refuse it |
| `EB-25` | **The withdrawn digest was not quietly restored.** An earlier round recorded a `source_sha256` computed over a markdown rendering rather than raw bytes; it was withdrawn, and the note recording that stays in the artefact. The digest now present is a different value over different bytes, and the record says so |

### 2.2 The mutable URL survives, still marked

`https://raw.githubusercontent.com/microsoft/electionguard-rust/main/…` remains
in the artefact as a `NON-AUTHORITATIVE NAVIGATION URL`, with
`human_readable_url_is_authoritative: false`. Now that a pinned URL sits beside
it, it is the one a hurried reader is most likely to copy, so the marking matters
more than it did before, not less.

---

## 3. What was never blocked, and was therefore never excused

| ID | Rule |
| -- | ---- |
| `EB-12` | **The normative provenance was present throughout.** `source.authoritative` names the ElectionGuard Design Specification v2.1.0 §3.1.1 p.14 at a **versioned release asset** — a tag, not a branch — with its SHA-256 in the artefact. Unchanged by this round |
| `EB-13` | **The parameter values never depended on either blocked path.** They are reconstructed **offline** from the published `ln 2` rule plus a recorded 279-bit offset, with `q`, `r` and `g` following in closed form. No file and no network is consulted. This is why the blockers cost provenance *traceability* and not parameter *correctness*, and why the pin adds traceability rather than confidence in the numbers |
| `EB-14` | **`AM-79` was corrected downward while the gap was open.** The blockers explained why the commit pin was missing; they did not entitle the acceptance matrix to claim it was present. It reads `SATISFIED` now on evidence, not on the mere disappearance of the blocker |
| `EB-15` | **Defect C was fully in scope for the blocked environment and was completed there.** No part of it was deferred |

---

## HISTORICAL FINDING — the blocked state, 2026-08-02

*Superseded by §1 and §2. Retained as the evidence that the blockers were
environmental. Commands were executed in the build environment on 2026-08-02 and
outputs are reproduced verbatim.*

| ID | Rule |
| -- | ---- |
| `EB-01` | **A blocker with no reproduction is indistinguishable from an excuse.** The commands were recorded so a reviewer with network access could run the same ones and see a different result, which is the only way to confirm the diagnosis was environmental. That is exactly what then happened |
| `EB-02` | **Nothing here was inferred.** No output was reconstructed from memory, and no error text was tidied up |

### H.1 Defect A — the declared but unlocked state

```console
$ grep -c 'name = "cryptography"' uv.lock
0
```

```console
$ uv lock
Using CPython 3.12.3 interpreter at: /usr/bin/python3.12
  × No solution found when resolving dependencies for split (markers:
  │ python_full_version >= '3.15'):
  ╰─▶ Because hypothesis was not found in the package registry and
      epd2-civic-os:dev depends on hypothesis>=6.112,<7, we can conclude that
      epd2-civic-os:dev's requirements are unsatisfiable.
      And because your workspace requires epd2-civic-os:dev, we can conclude
      that your workspace's requirements are unsatisfiable.

      hint: An index URL (https://pypi.org/simple) could not be queried due to
      a lack of valid authentication credentials (403 Forbidden).
EXIT=1
```

```console
$ uv sync --all-groups --frozen
  × Failed to download `jsonschema==4.26.0`
  ╰─▶ HTTP status client error (403 Forbidden) for url
      (https://files.pythonhosted.org/packages/69/90/.../jsonschema-4.26.0-py3-none-any.whl)
EXIT=1
```

```console
$ curl -sS https://pypi.org/simple/cryptography/
Host not in allowlist: pypi.org. Add this host to your network egress settings to allow access.

$ curl -sS -o /dev/null -w '%{http_code}\n' https://files.pythonhosted.org/
403
```

| ID | Rule |
| -- | ---- |
| `EB-03` | **The failure was on `hypothesis`, not on `cryptography`,** and that detail mattered. `uv lock` re-resolves the **entire workspace**; it never reached the new dependency because it could not resolve the existing ones. This is also why no partial or targeted lock update was attempted |
| `EB-04` | The operative line was the hint: `An index URL (https://pypi.org/simple) could not be queried due to a lack of valid authentication credentials (403 Forbidden)` |
| `EB-05` | **No user data and no global environment was removed.** The `rm -rf .venv` applied to a build directory inside that working tree |
| `EB-06` | **Every workspace member built.** uv got as far as building all twenty-two workspace packages and then failed downloading a **third-party wheel** — evidence the lock was structurally usable, not that a regenerated one would resolve |
| `EB-07` | **`FROZEN CLEAN INSTALL: NOT EXECUTED`** was recorded at the time. A run that ends in a 403 is not a failed pass, it is an absent one. It has since been executed on a network-enabled host — see §1.1 |
| `EB-08` | **That was an allowlist, not an outage.** The proxy named the remedy in its own message |

### H.2 Defect B — four refused access paths

```console
$ curl -sS 'https://api.github.com/repos/microsoft/electionguard-rust'
{"message":"GitHub access to this repository is not enabled for this session.
 Use add_repo to request access. ..."}

$ curl -sS https://raw.githubusercontent.com/microsoft/electionguard-rust/main/src/eg/src/standard_parameters.rs
curl: (56) CONNECT tunnel failed, response 403

$ git clone --filter=blob:none https://github.com/microsoft/electionguard-rust /tmp/eg-probe
fatal: unable to access 'https://github.com/microsoft/electionguard-rust/':
The requested URL returned error: 403

$ curl -sS -o /dev/null -w '%{http_code}\n' https://cdn.jsdelivr.net/gh/microsoft/electionguard-rust@main/README.md
curl: (56) CONNECT tunnel failed, response 403
```

| ID | Rule |
| -- | ---- |
| `EB-09` | **Two distinct mechanisms, so it was not one misconfiguration.** `api.github.com` was gated per-repository by an access broker; `raw.githubusercontent.com` by the egress allowlist. Both had to be opened, and both since were |
| `EB-10` | **No commit SHA and no byte-exact digest could be obtained, and neither was invented.** `upstream_commit`, `commit_pinned_source_url` and `source_sha256` stayed explicitly `null`, each with a stated reason, until real values existed |
| `EB-11` | **A markdown-rendering fetch was not accepted as a substitute.** An earlier round recorded a `source_sha256` computed over a converted rendering rather than the raw bytes; that digest was **withdrawn**. A digest over the wrong bytes is worse than no digest, because a reader will check it, find a mismatch, and have no way to tell which artefact is wrong |
| `EB-16` | **The upstream repository was not to be cloned into this tree,** and was not. The archive excludes downloaded source repositories; the requirement was a commit hash and a digest, not a vendored copy. It remains excluded now that the pin exists |

---

## 4. What this document does not decide

```text
Whether the parameters are correct        -> established offline; see the
                                             derivation block, not this file
Whether VO-08 can be closed               -> PACK-16B review, PACK-17
Whether PACK-16D is acceptable            -> independent audit
Whether the resolving evidence suffices   -> the reviewer's call, on the
                                             values above rather than on
                                             this round's word for it
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
