# PACK-16D — Handover

**Round:** PACK-16D — Final Two-Line Documentation Consistency Correction. A
documentation-only correction of the network-enabled finalization candidate, not
a new round. **No code, no lock file, no artefact, no test, no matrix row and no
open decision was touched.**
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Status block

```text
PACK-16D FINAL ACCEPTANCE CANDIDATE

DOCUMENTATION CONSISTENCY:
PASS

NETWORK-DEPENDENT FINALIZATION:
COMPLETE

CHECKPOINT SIGNATURE PROVIDER:
CRYPTOGRAPHY ED25519

HANDWRITTEN ED25519:
ABSENT

CRYPTOGRAPHY DEPENDENCY:
DECLARED AND LOCKED

RESOLVED CRYPTOGRAPHY VERSION:
46.0.7

CLEAN FROZEN SYNC:
PASS ON NETWORK-ENABLED HOST - NOT RE-RUN IN THE BUILD SESSION

ELECTIONGUARD 2.1 NORMATIVE SOURCE:
PINNED

ELECTIONGUARD-RUST CORROBORATING SOURCE:
COMMIT-PINNED

UPSTREAM COMMIT:
520651138110a13f777409e96606454df928ceac

UPSTREAM SOURCE SHA-256:
ad38bfa68d31131a7d721e08d359224b21e967aae4d517534a60a109e10f5770
RECORDED IN EPD2-CRYPTO-1 PARAMETER ARTIFACT; COMPUTED ON THE
NETWORK-ENABLED HOST AND NOT RE-FETCHED IN THE BUILD SESSION

PARAMETER DIGEST:
RECOMPUTED AND VERIFIED

PARAMETER VALUES:
RECONSTRUCTED OFFLINE FROM THE PUBLISHED RULE

TARGET-PROFILE CROSS-IMPLEMENTATION CORE:
PASS

3-OF-5 THRESHOLD PATH:
PASS

4-OF-7 CONFIGURATION:
PASS

CHECKPOINT AUTHENTICITY:
PASS

CRYPTOGRAPHIC AND TARGET-PROFILE IMPLEMENTATION:
UNCHANGED

FULL ELECTIONGUARD ECOSYSTEM INTEROPERABILITY:
DEFERRED TO PACK-17

FULL INDEPENDENT VERIFIER:
DEFERRED TO PACK-17

CONSTANT-TIME PRODUCTION ASSURANCE:
NOT CLAIMED

VO-08:
OPEN

REPOSITORY_VERSION:
0.16.0

CANON_VERSION:
0.8.0

ADR-102:
PROPOSED

NOT FINAL PASS
NOT CERTIFIED
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
INDEPENDENT FINAL ACCEPTANCE REVIEW REQUIRED
PACK-17 MUST NOT START BEFORE IT
```

### 1.0 What this correction changed

Two sentences, in two documents. An audit passed every substantive finding and
returned `DOCUMENTATION CONSISTENCY: NARROW FAIL — TWO STALE SENTENCES`: this
handover's checkpoint-signature evidence table still denied that the provider
was in the lock file, and `LD-07` in the dependency assessment still described
the lock pinning of the declared range as unfinished. Both had been true two
rounds earlier and were false by the time they were read.

| Where | Was | Is |
| -- | --- | --- |
| §6, dependency status | declared in the service manifest, and asserted **absent from the lock**, citing `OD-P16D-16` | `declared in services/voting-service/pyproject.toml; resolved in uv.lock as cryptography 46.0.7; clean frozen sync completed on the network-enabled host` |
| `LD-07` | no Git or branch source, but the lock pinning of the declared range described as **still owed**, filed as a separate defect | `The released version range is now resolved and hash-pinned in uv.lock as cryptography 46.0.7; §4 records the regeneration and the checks run against it` |

**The two superseded sentences are described here rather than reproduced.** A
grep for either of them across this tree must return nothing, and quoting them
verbatim in a correction record — even in a column headed *Was* — would defeat
the check a reviewer will actually run. The exact prior bytes are recoverable
where they belong: in the source archive
`f5643e07b7d896b49d1a732cca314892566108929a567fff85202b6f64602335`, against
which this tree diffs in these two files and nothing else.

Neither is a new fact. Both were already recorded correctly in §8.1 of this
handover, in §4.1 of the dependency assessment, in `AM-89`, in `OD-P16D-16` and
in the lock file itself — which is exactly what made them worth fixing rather
than shrugging at. **A document that states a resolved defect as current in one
table while denying it in another is not a smaller problem than a document that
is simply wrong; it is a larger one**, because a reader has no way to tell which
sentence is the stale one without going to the lock file. The previous round's
own defect was a status drifting ahead of its evidence. This is the same class
of error with the sign flipped: prose lagging behind the facts.

**No historical note was added.** One was permitted and is not useful here: the
lock's history is already told at length, with verbatim transcripts, in
`PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md` and in `OD-P16D-16`. Repeating it in
a capability table would put the same claim in two places with two lifetimes,
which is how this pair of sentences went stale in the first place.

### 1.1 Two lines in that block are narrower than they look

`CLEAN FROZEN INSTALL: PASS` and `UPSTREAM SOURCE SHA-256: RECORDED` are both
qualified above rather than in a footnote, because a status block is the part
of a handover most likely to be quoted alone.

`uv lock` and `rm -rf .venv && uv sync --all-groups --frozen`
(`Checked 61 packages`) were executed on a host with network access. The
session that produced this candidate has no package index and did not re-run
them. What that session establishes instead is that the lock's parsed contents
are well-formed and in the right dependency graph, and that the `cryptography`
build the test suite imports is version-identical to the locked resolution.

The upstream file's digest was likewise computed on that host. This session
verified the pin's internal consistency — full 40-character lower-case object
id, pinned URL containing that exact commit and that exact path, 64 lower-case
hex digest — and re-derived every parameter offline. It did not re-fetch the
bytes, `source_sha256_verification_scope` in the parameter artefact says so,
and one command settles it: `curl -sL <pinned-url> | sha256sum`.

Neither qualification is a reason to withhold the status. Both are the reason
the status is worth something.

### 1.2 What this round did and did not do

Two audit findings had been recorded as environmental blockers rather than
worked around, each with verbatim transcripts and the exact command that would
close it. Those commands were run on a host with the required access.

| Audit finding | Outcome |
| --- | --- |
| `DEPENDENCY LOCK / FROZEN INSTALL: FAIL` | **RESOLVED.** `uv.lock` regenerated by `uv lock`; `cryptography 46.0.7` resolves from `https://pypi.org/simple` with `sha256:` hashes on all 43 artefacts and both transitives, inside the `epd2-voting-service` graph. Not hand-edited, and a test asserts the entry has the shape a resolver produces |
| `IMMUTABLE PARAMETER PROVENANCE: FAIL` | **RESOLVED.** `microsoft/electionguard-rust` at `520651138110a13f777409e96606454df928ceac` (2025-02-02), `src/eg/src/standard_parameters.rs`, raw-byte SHA-256 `ad38bfa6…5770`, retrieved 2026-08-03, recorded beside the already-pinned normative specification and not in place of it |
| `ACCEPTANCE MATRIX: NARROW CORRECTION REQUIRED` | **ALIGNED.** `AM-79` and `AM-89` promoted to `SATISFIED` against the five conditions each requires, every one asserted by a named offline test |

**No cryptographic work was done.** No algorithm, guardian path, checkpoint
semantic, atomic transaction, sealed-batch rule or conformance oracle was
touched. What changed is `uv.lock`, the parameter artefact's provenance
metadata, two test modules that stopped tolerating the blocked state, and the
documentation set.

**The promotions were earned, not inherited from the blocker's removal.** The
previous correction's defect was a status drifting ahead of its evidence;
promoting a row because an obstacle disappeared would be the same error pointed
the other way. Each of the ten conditions across the two rows is asserted by a
test that fails if the field goes missing, is truncated to an abbreviated hash,
points at a different commit than the URL beside it, or is accompanied by a
leftover excuse for not having it.

**One transcription discrepancy is recorded rather than silently corrected.**
The finalization brief quoted the new `uv.lock` digest as `02d0775458…`; the
digest computed over the delivered file's actual bytes is `b2d0775458…`. The
two agree in 63 of 64 hex characters, which no byte-level corruption produces.
It is a transcription slip in the brief, and the computed value governs because
it is the one anybody can reproduce from the file.

## 2. Archive evidence

| Field | Value |
| --- | --- |
| Source archive | `EPD2_PACK-16D_CRYPTOGRAPHIC_IMPLEMENTATION_ATOMIC_PERSISTENCE_TEST_VECTORS_AND_VERIFICATION_HARNESS_FINAL_CORRECTED_CANDIDATE.zip` |
| Source SHA-256 | `f5643e07b7d896b49d1a732cca314892566108929a567fff85202b6f64602335` |
| Source state | Every substantive finding passed; `DOCUMENTATION CONSISTENCY: NARROW FAIL — TWO STALE SENTENCES` |
| Output archive | `EPD2_PACK-16D_CRYPTOGRAPHIC_IMPLEMENTATION_ATOMIC_PERSISTENCE_TEST_VECTORS_AND_VERIFICATION_HARNESS_FINAL_ACCEPTANCE_CANDIDATE.zip` |
| Final physical ZIP SHA-256 | **PUBLISHED EXTERNALLY WITH DELIVERY** |
| `uv.lock` SHA-256 | `b2d0775458d3b6e81d321724530c7a473584fb2b3d9d231d220d8e9dcdfe8066`, **unchanged** |
| Repository version before / after | `0.16.0` / `0.16.0`, unchanged |
| Canon version | `0.8.0`, unchanged |
| `ADR-102` / `VO-08` | `proposed` / `OPEN`, unchanged |

**Provenance of the earlier archives, so the chain stays readable:**
`..._ENVIRONMENT_BLOCKED_CANDIDATE.zip` (`a6fc8b67…b947c`) → network-enabled
finalization → `..._FINAL_CORRECTED_CANDIDATE.zip` (`f5643e07…2335`) → this
two-sentence correction → `..._FINAL_ACCEPTANCE_CANDIDATE.zip`.

**The archive is named `FINAL_ACCEPTANCE_CANDIDATE` because it is what goes to
final acceptance review, not because it has passed one.** Earlier names in this
chain tracked state deliberately — `ENVIRONMENT_BLOCKED_CANDIDATE` while two
blockers were open, `FINAL_CORRECTED_CANDIDATE` once they were closed — because
a filename is the first thing a reviewer reads and the last thing anyone
updates. **This is still not a PASS, not certified, and not production ready.**

**The working tree was verified byte-identical to the source archive before
anything was changed** — 1 368 files, every digest matching. A correction that
silently inherited other edits would be impossible to review at this scale, so
the check ran first and is reported first.

## 3. File inventory

**Documentation only.** No code, no lock file, no parameter artefact, no test,
no acceptance-matrix row, no open decision, no Canon file and no version
constant was touched.

| Class | Count |
| --- | --- |
| Added | **0** |
| Deleted | **0** |
| Modified | **2** — one sentence in each |

```text
docs/packs/PACK-16/PACK-16D-HANDOVER.md
    §6  dependency status line: the clause denying the lock entry ->
        resolved in uv.lock as cryptography 46.0.7
    §1  status block -> FINAL ACCEPTANCE CANDIDATE, DOCUMENTATION
        CONSISTENCY: PASS, and the upstream digest spelled out in full
    §1.0 new: what this correction changed, and why no historical note
    §2  archive evidence: source/output names, digests, provenance chain
    §3  this inventory

docs/packs/PACK-16/PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md
    LD-07: the clause describing the lock pinning as still owed ->
           resolved and hash-pinned in uv.lock as cryptography 46.0.7
```

**Two files, and no third.** `CHANGELOG.md` was deliberately not touched: its
`FINAL CORRECTED CANDIDATE` entry already describes the lock as regenerated and
`cryptography 46.0.7` as resolved, so it was never among the stale statements
and editing it would have added a modified file without correcting anything.
The same reasoning kept the Master Register, `ADR-102`, the acceptance matrix
and the open decisions out of this diff — each was already right.

**Unchanged and verified unchanged after the edits:** `uv.lock`
(`b2d0775458…8066`), `package-lock.json`,
`services/voting-service/pyproject.toml`,
`reference/crypto/profiles/EPD2-CRYPTO-1.json`, every module under
`reference/`, every test, `PACK-16D-ACCEPTANCE-MATRIX.md`,
`PACK-16D-OPEN-DECISIONS.md`, everything under `docs/canonical/`,
`REPOSITORY_VERSION` `0.16.0`, `CANON_VERSION` `0.8.0`, `ADR-102` `proposed`,
`VO-08` `OPEN`.

For the file-by-file record of the *previous* round — the one that regenerated
the lock and pinned the upstream source — see
`PACK-16D-IMPLEMENTATION-REPORT.md` §2. What follows is that round's inventory,
retained because this correction changed none of it.

Exact diff — modified:

Exact diff — modified:

```text
uv.lock                                            1a1e5a72...d543
                                                -> b2d07754...8066
    + cryptography 46.0.7   registry source, 43 hashed artefacts
    + cffi 2.1.0            OpenSSL binding layer
    + pycparser 3.0         cffi's C parser
    149 lines added, 0 removed, 0 existing versions changed.
    Supplied already regenerated; verified here by parsing, not by grep.

services/voting-service/src/epd2_voting_service/reference/crypto/profiles/EPD2-CRYPTO-1.json
    + source.corroborating.upstream_commit         520651138110a13f...ceac
    + source.corroborating.upstream_commit_date    2025-02-02T22:17:21-08:00
    + source.corroborating.commit_pinned_source_url
    + source.corroborating.source_sha256           ad38bfa6...5770
    + source.corroborating.source_sha256_verification_scope
    + source.corroborating.retrieval_date          2026-08-03
    - source.corroborating.unpinned_reason         removed with the pin
    - source.corroborating.auditor_action          removed with the pin
    ~ source.corroborating.provenance_status       -> SATISFIED
    ~ source.hierarchy.corroborating_implementation -> PINNED
    ~ digests.source_sha256 / source_sha256_status -> RECORDED
    = human_readable_url_is_authoritative          STILL false
    = withdrawn_digest_note                        KEPT
    = parameter_digest                             UNCHANGED, still recomputes

services/voting-service/tests/reference/test_epd2_crypto_1.py        30 -> 32
    the nine required provenance tests normalized to their exact names;
    every dual-state branch removed; +source_file_path_present;
    +specification_sha256_present split out from the upstream-digest check
tests/repository/test_pack16d_signature_dependency.py                 7 -> 9
    every dual-state branch removed; +is_in_the_voting_service_graph;
    +blocked_evidence_is_marked_resolved; the provider's imported version
    now asserted equal to the locked resolution
services/voting-service/tests/reference/vectors/PACK-16D-TARGET-PROFILE-TIMINGS.json
    regenerated by the conformance run; timings only, no fixture changed

docs/packs/PACK-16/PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md   -> RESOLVED
docs/packs/PACK-16/PACK-16D-ACCEPTANCE-MATRIX.md              AM-79, AM-89
docs/packs/PACK-16/PACK-16D-OPEN-DECISIONS.md                 OD-P16D-16/-17 CLOSED
docs/packs/PACK-16/PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md
docs/packs/PACK-16/PACK-16D-PARAMETER-PROFILE-IMPLEMENTATION.md
docs/packs/PACK-16/PACK-16D-PROTOCOL-EVIDENCE-MATRIX.md
docs/packs/PACK-16/PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md
docs/packs/PACK-16/PACK-16D-CHECKPOINT-SIGNATURE-AND-SIGNER-TRUST-MODEL.md
docs/packs/PACK-16/PACK-16D-SECURITY-AND-SIDE-CHANNEL-LIMITATIONS.md
docs/packs/PACK-16/PACK-16D-CRYPTOGRAPHIC-MODULE-MAP.md
docs/packs/PACK-16/PACK-16D-FIR-COVERAGE-MATRIX.md
docs/packs/PACK-16/PACK-16D-IMPLEMENTATION-REPORT.md
docs/packs/PACK-16/PACK-16D-HANDOVER.md
docs/packs/PACK-16/PACK-16D-CANON-ASSESSMENT.md               round header only
docs/packs/PACK-16/PACK-16D-TEST-VECTOR-CATALOG.md            round header only
docs/packs/PACK-16/PACK-16D-REFERENCE-VERIFIER.md             round header only
docs/adr/ADR-102-...md
docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md    section 1.27 added
CHANGELOG.md
```

**`package-lock.json` is unchanged**, correctly: no Node dependency exists and
the Node oracle imports only `node:` builtins.
`services/voting-service/pyproject.toml` is unchanged from the source
candidate — `cryptography>=46.0.7,<47` was already declared and the range did
not need to move. **No migration, API implementation, event schema, frontend
file, CI workflow or version constant was touched, and no file under
`docs/canonical/` was modified.**

## 4. `EPD2-CRYPTO-1` — provenance, digests and validation

### 4.1 Source hierarchy, now declared rather than inferred

| Level | Value | State |
| --- | --- | --- |
| **Normative** | ElectionGuard Design Specification **v2.1.0**, §3.1.1 p.14 | **PINNED** |
| Document URL | `https://github.com/microsoft/electionguard/releases/download/v2.1/EG_Spec_2_1.pdf` — a versioned release asset under tag `v2.1`, not a branch | **PINNED** |
| Specification SHA-256 | `a263ab3cd2cf28f05de324ecd2d9752ffed45f814709582b4c2bb23d1826b936`, **recorded in the artefact** | inherited from PACK-16B `F-01`, **not re-verified this round** |
| **Corroborating implementation** | `microsoft/electionguard-rust`, `src/eg/src/standard_parameters.rs` | **NOT PINNED** |
| `upstream_commit` | `null` | **NOT RECORDED — BLOCKED BY ENVIRONMENT** |
| `commit_pinned_source_url` | `null` | **NOT RECORDED** |
| `source_sha256` | `null`, with `source_sha256_status: NOT RECORDED` | **NOT RECORDED** |
| Mutable `/main/` URL | present, `human_readable_url_is_authoritative: false` | non-authoritative |
| **Local immutable artefact** | `EPD2-CRYPTO-1.json` | present |
| `parameter_digest` | `f0af5b71412ccf93a1eaf93364c223f5339cdb2815a2efcfa1bd775cd2bf17fb` | **RECOMPUTED AND VERIFIED** |

`source.corroborating.role` states in the artefact that it "is NOT a
substitute for the normative specification and is not authoritative for any
value here", and `is_normative` is `true` on one block and `false` on the
other. `test_epd2_crypto_1_normative_and_corroborating_sources_distinct`
asserts all of it.

**Overall: `IMMUTABLE UPSTREAM IMPLEMENTATION PROVENANCE: PARTIALLY
SATISFIED`.** The normative half is pinned; the implementation half is not.
Averaging the two into a pass is what `AM-79` did wrong.

### 4.2 The implementation source, now commit-pinned

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

For two rounds this section explained why the pin could not be obtained: four
access paths refused by two distinct mechanisms — a per-repository access broker
on `api.github.com`, the egress allowlist on `raw.githubusercontent.com`,
`git clone` and the CDN mirrors. **No commit SHA and no digest was ever
invented**, and the artefact carried three explicit `null`s with a stated reason
instead. The transcripts remain in `PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md`
as a `HISTORICAL FINDING`.

`unpinned_reason` and `auditor_action` were removed in the same change that
added the pin — `test_epd2_crypto_1_source_commit_present` fails if a pin and an
excuse for having no pin are ever both present. An earlier round's `3afa2962…`
digest — computed over a markdown rendering rather than raw bytes — stays
**WITHDRAWN** and was not restored; the digest above is a different value over
different bytes, and the artefact's `withdrawn_digest_note` says which is which.

**The digest was computed on the network-enabled host.** This session verified
the pin's internal consistency and re-derived every parameter offline; it did
not re-fetch the bytes, and `source_sha256_verification_scope` records that in
the artefact. One command closes it: `curl -sL <pinned-url> | sha256sum`.

### 4.3 What the values rest on instead

```text
p = ONES(256) || M(3584) || ONES(256)                     4096 bits
M = (first 3305 fractional bits of ln 2) << 279 | delta_low
delta_low = 0x445744fb5f2da4b751005892d356890defe9cad9b9d4b713e06162a2d8fdd0df2fd608
q = 2**256 - 189
r = (p - 1) // q
g = pow(2, r, p)
```

`ln 2` is computed locally as `2·atanh(1/3)`, not tabulated. All four
constants reconstruct exactly, with no file and no network consulted.

**This is why the missing pin cost traceability and not correctness — and why
having it now changes the trail rather than the confidence.** A reader can
re-fetch the exact bytes the constants were first read from, which is worth
having; the values themselves were, and remain, established by the normative
specification and by reconstruction from the published rule. `AM-79` is
`SATISFIED` because every provenance field it requires is present and tested,
not because the numbers became more trustworthy this week.

Validation on load is unchanged and fail-closed: bit lengths from code,
`q = 2²⁵⁶−189`, `q | p−1`, `p = qr+1`, `1 < g < p`, `g^q = 1`, `p`/`q`/`r/2`
probable prime, both 256-bit one-runs, offline reconstruction, `g = 2^r mod p`,
`r = (p−1)/q`, artefact self-digest, pinned digest, filename binding.

## 5. Guardian evidence

| Field | Value |
| --- | --- |
| Module paths | `reference/guardians/ceremony.py`, `reference/guardians/threshold.py` |
| Scheme | Feldman verifiable secret sharing with Schnorr proof of possession; Shamir threshold decryption in the exponent |
| Default quorum | **3-of-5** — succeeds at `(1,2,3)`, `(1,3,5)`, `(3,4,5)`, `(2,4,5)` |
| High-assurance | **4-of-7** — succeeds at `(1,2,3,4)`, `(2,4,6,7)`, `(1,3,5,7)` |
| Quorum rejection | 2-of-5 and 3-of-7 refused with `guardian.insufficient_quorum`; `QuorumPolicy` additionally rejects `2k ≤ n` |
| Share rejection | duplicate, invalid-proof, unknown-guardian, wrong-election and wrong-ciphertext shares each refused with their own reason code |
| Threshold reduction | impossible — the quorum comes from the ceremony transcript, and a rewritten transcript fails `verify_ceremony` |
| Compensated decryption | `compensated_decryption_share()` exists only to raise `CompensatedDecryptionProhibited` |
| Secret leakage | a test searches the transcript's canonical bytes for every share and coefficient |
| On the real profile | a 3-of-5 ceremony and a full record verification both run on `EPD2-CRYPTO-1` |
| Test results | `test_guardians.py` **28 passed**; `test_e2e.py::test_e2e_11`, `::test_e2e_12` pass |

## 6. Checkpoint signature evidence

| Field | Value |
| --- | --- |
| Provider | **`cryptography` 46.0.7**, linked against OpenSSL **3.5.6 (7 April 2026)** |
| Licence | Apache-2.0 / BSD-3-Clause, at the user's option |
| Scheme | Ed25519, RFC 8032 PureEdDSA over edwards25519 with SHA-512 |
| Abstraction | `CheckpointSignatureProvider` Protocol, six operations; one implementation, `CryptographyEd25519Provider`; module-level singleton `PROVIDER` |
| API used | `Ed25519PrivateKey.from_private_bytes` / `.public_key()` / `.sign()`; `Ed25519PublicKey.from_public_bytes` / `.verify()` / `.public_bytes(Raw, Raw)` — six calls, one module |
| Hand-written path | **REMOVED.** `crypto/ed25519.py` deleted |
| Fallback | **NONE.** The library is imported at module scope; absence raises `SignatureProviderUnavailableError` at import time |
| Canonical encodings | raw 32-byte public key, raw 64-byte signature, exact lengths only — no PEM, no DER, no base64 |
| Verification | fail-closed, returns `False` on every defect, never raises on bad input |
| Trust decisions | **none in the provider.** Signer authorisation stays in `SignerRegistry` and the election context |
| Dependency status | declared in `services/voting-service/pyproject.toml`; **resolved in `uv.lock` as `cryptography 46.0.7`**; clean frozen sync completed on the network-enabled host |

**Unchanged from the accepted round** — the audit passed
`CHECKPOINT SIGNATURE SEMANTICS`, and nothing below moved:
the canonical payload's ten bound fields, `EPD2-CHECKPOINT-2`, the
`BOARD_CHECKPOINT` domain separation, the `SignerRegistry` trust anchor
supplied alongside the export, the declared-in-advance rotation windows, the
five distinct failure outcomes and their exit codes 45–49, and the
separation of authenticity from consistency.

**RFC 8032 conformance:** three published §7.1 vectors — TEST 1 (empty
message), TEST 2 (one byte), TEST 3 (two bytes) — each checked for derived
public key, produced signature and verification.

**Independent oracle:** the OpenSSL **command-line binary** (3.0.13), run
out-of-process, importing no cryptographic Python library — a raw key is
wrapped in its twelve fixed DER prefix bytes by hand. Six cases: three RFC
vectors accepted, three mutated-message variants rejected.

**Stated limitation, because it is the honest weak point:** the CLI and the
library the provider links share an upstream project, so a defect present in
both builds would be invisible to that comparison. The evidence that does
**not** share a lineage is the RFC 8032 published vectors, which is why they
are now the primary evidence for the primitive and the CLI is corroboration.

**Test results:** `test_checkpoint_signatures.py` — **44 passed**, including
`test_vetted_ed25519_provider_is_active`,
`test_handwritten_ed25519_not_imported` (an `ast` walk over every module in
`reference/`) and `test_missing_provider_fails_closed` (a blocked-import
subprocess preceded by a control run, so it cannot pass for the wrong
reason).

## 7. Conformance evidence

Five classifications now, not three. The split is the audit's finding made
structural: one `cross-implementation` label covering both profiles is
exactly how it stayed invisible that most checks ran on the fast group.

| Class | Count |
| --- | --- |
| `internal-stability` | **0** in this catalogue — deliberately. The 23 stability vectors live in `PACK-16D-TEST-VECTORS.json` and are never promoted here |
| `primary-source` | **1** — the ElectionGuard 2.1 standard baseline parameters |
| `rfc-conformance` | **1** — RFC 8032 §7.1, three vectors |
| `cross-implementation-test-profile` | **8** |
| `cross-implementation-target-profile` | **16** |
| **Total in `PACK-16D-CONFORMANCE-EVIDENCE.json`** (`EPD2-CONFORMANCE-2`) | **26** |

### 7.1 The target-profile core — all twelve operations on `EPD2-CRYPTO-1`

```text
parameter digest            group element encoding      scalar encoding
selection encryption        selection proof             ballot hash
confirmation code           accumulation                guardian public commitment
decryption share            3-of-5 combination          aggregate tally recovery
```

Plus **two invalid fixtures**, each with a share multiplied by `g` so it
stays **inside the subgroup** — refused by the mathematics rather than by a
cheap structural check that a random value would also have failed.

- **Determinism:** fixed nonces, fixed scalars, fixed plaintexts, fixed
  election context, fixed manifest, fixed guardian polynomials. Comparing
  two independently randomised ciphertexts would prove nothing.
- **Exported fixtures:** `PACK-16D-TARGET-PROFILE-FIXTURES.json`, 12 cases,
  `contains_secret_material: false`.
- **Machine-readable results:** every oracle verdict carries `vector_id`,
  `operation`, `profile_id`, `expected`, `actual`, `match`,
  `oracle_version`.
- **One documented command:**
  `pytest -m slow_conformance services/voting-service/tests/reference/`
  → `15 passed, 484 deselected in 9.05s`.

### 7.2 The oracle rebuilds the encoding, it is not handed it

The `ballot_structural` handler is given the ballot's **fields** and
reconstructs the canonical bytes from the written grammar before hashing
them, then derives the confirmation code from its own reconstruction. The
weaker form — handing it the producer's canonical bytes — would test the
hash and not the encoding, and the encoding is where the previous round's
real defect was found.

### 7.3 Independence, asserted structurally

`test_oracle_imports_no_producer_code` fails if the oracle imports anything
but `node:` builtins, or mentions `epd2_voting_service`, `python`,
`child_process` or `encode_struct`. It implements its own
square-and-multiply modular exponentiation and its own canonical encoder.

**What it still is not:** a complete second ElectionGuard implementation,
and it shares an author with the producer even though it was written from
the written grammar. `OD-P16D-02` stays open, and §16 asks an auditor to
attack exactly that.

**Timings** (measured, seconds): the oracle runs the entire twelve-operation
target-profile core in **0.579 s**. Producer-side generation on the real
group: ceremony 1.968, ballot encryption 0.542, accumulation 0.111,
selection proof 0.081, selection encryption 0.041. Full target suite 8.06 s.

## 8. Language, dependencies and lock files

| Field | Value |
| --- | --- |
| Language | Python ≥3.12, the repository's existing stack |
| Dependency changes | **one added**: `cryptography>=46.0.7,<47`, in `services/voting-service/pyproject.toml` |
| `pyproject.toml` (root) | unchanged — the provider belongs to the package that imports it |
| `uv.lock` | **REGENERATED** — see below |
| `package-lock.json` | unchanged, correctly — no Node dependency exists |

The previous round's headline was "zero new dependencies", presented as the
strongest form of compliance. It was not. The way that claim stayed true was
by implementing Ed25519 here, and an audit failed it. **The right target was
never "add no dependency" — it was "implement no cryptographic
primitive".** Those two pointed in opposite directions and the round had
chosen the weaker one without noticing.

Everything else remains standard library: `hashlib`, `hmac`, `secrets`,
`threading`, `dataclasses`, `enum` and Python's arbitrary-precision
integers. Exactly one module in `reference/` imports a third party, and an
`ast` test fails if a second one does.

### 8.1 DEPENDENCY LOCK: REGENERATED

```text
DEPENDENCY LOCK:
REGENERATED

FROZEN CLEAN INSTALL:
PASS - EXECUTED ON A NETWORK-ENABLED HOST
```

| Field | Value |
| --- | --- |
| Declared range | `cryptography>=46.0.7,<47`, in `services/voting-service/pyproject.toml`, unchanged |
| **Resolved version** | **46.0.7**, satisfying every clause of the declared specifier |
| `uv.lock` entry | **PRESENT**, with `source = { registry = "https://pypi.org/simple" }` and `sha256:` hashes on all 43 artefacts. Confirmed by parsing the lock as TOML, not by string search |
| Dependency graph | `cryptography` is in `epd2-voting-service`'s own `dependencies`, and its `requires-dist` specifier echoes the manifest — not a stray root-level entry |
| `uv.lock` SHA-256 before | `1a1e5a72b67b92a53b189e6eb9c9f4305f236a0aa76f7d55887f24ad2a76d543` |
| `uv.lock` SHA-256 after | `b2d0775458d3b6e81d321724530c7a473584fb2b3d9d231d220d8e9dcdfe8066` |
| New transitive packages | **two**: `cffi 2.1.0` (the binding layer to OpenSSL) and `pycparser 3.0` (`cffi`'s own C parser). Both locked with artefact hashes |
| Lock delta | 149 lines added, 0 removed, **0 existing package versions changed**; `requires-python` and the lock revision unchanged |
| Provider import path | `epd2_voting_service.reference.crypto.signature_provider` |
| Frozen install result | `Checked 61 packages` — 62 lock entries less the workspace root, which is not installed as a distribution |

**Run on a network-enabled host:**

```console
$ uv lock
$ rm -rf .venv
$ uv sync --all-groups --frozen
Checked 61 packages
```

**The lock digest in the finalization brief differs from the file's.** The
brief quoted `02d0775458…`; the digest computed over the delivered bytes is
`b2d0775458…`. The two agree in 63 of 64 hex characters, which no byte-level
corruption produces — SHA-256 avalanche makes a one-nibble difference about as
likely as guessing the digest outright. It is a transcription slip, it is
recorded rather than quietly reconciled, and the computed value governs because
it is the one anybody can reproduce from the file.

**What the build session did and did not verify.** It parsed the lock and
checked every property in the table above, and it asserted that the
`cryptography` the suite imports is version-identical to the locked resolution —
which ties the exercised code to the recorded resolution. It has no package
index and did **not** re-run `uv sync`. "The tests are green" and "the frozen
install passes" are two claims, and this handover keeps them apart.

**Held open by tests, not by this paragraph.**
`tests/repository/test_pack16d_signature_dependency.py` — 9 tests, parsing
`uv.lock` with `tomllib` — fails if the provider is missing from the lock, if
an entry appears without a registry source and `sha256:`-prefixed hashes (the
shape a hand-edit would produce), if the resolved version falls outside the
declared range, if `cryptography` is locked but is not a dependency of
`epd2-voting-service`, or if the outstanding-lock notice outlives the lock it
described.

The two out-of-process test oracles — the `openssl` binary (3.0.13) and
Node.js (v22.22.2) — remain **not** repository dependencies and appear in no
lock file.

## 9. Cryptographic module list

```text
crypto/domain_separation.py   EPD2-DS-1, 27 labels, one registry
crypto/encoding.py            EPD2-ENC-1, canonical binary tuples
crypto/hashing.py             HMAC-SHA-256, 32 bytes, never truncated
crypto/randomness.py          production CSPRNG; two-guard test source
crypto/parameters.py          validation, profile registry, bit lengths in code
crypto/elgamal.py             exponential ElGamal, accumulation, bounded decode
crypto/proofs.py              disjunctive CP, contest sum CP, decryption share CP
crypto/merkle.py              RFC 6962 tree, inclusion and consistency proofs
crypto/signature_provider.py  PORT over a vetted library - no arithmetic here
guardians/ceremony.py         Feldman VSS DKG, quorum policy
guardians/threshold.py        Shamir in the exponent, Lagrange at zero
publication/checkpoint_signing.py   canonical payload, signer trust anchor
testing/conformance.py        five evidence classes

crypto/profiles/EPD2-CRYPTO-1.json                              REAL
crypto/profiles/EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256.params   TEST ONLY
crypto/profiles/EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160.params   TEST ONLY

DELETED: crypto/ed25519.py
```

**Nine modules carry cryptographic constructions and one carries a
primitive.** The distinction is worth stating: ElGamal, the proof family,
the Merkle tree and the canonical encoder are protocol *constructions* over
standard-library primitives — they are what this reference implementation
exists to make readable. Ed25519 is a *primitive*, and primitives are not
this repository's to write.

## 10. Schema list

13 versioned schemas in `EPD2-SCHEMA-1`: `parameter_set`,
`election_context`, `manifest`, `encrypted_ballot`, `spoiled_ballot`,
`receipt`, `batch_commitment`, `batch_opening`, `reconciliation_record`,
`board_entry`, `checkpoint`, `election_record`, `verification_result`.

## 11. Test and evidence counts

| Field | Value |
| --- | --- |
| Stability vectors | **23** — self-generated, stability only, unchanged |
| Conformance entries | **26** — 1 primary-source, 1 rfc-conformance, 8 cross-implementation-test-profile, 16 cross-implementation-target-profile |
| Target-profile core operations cross-checked | **12 of 12**, plus 2 invalid fixtures |
| Negative vectors | **39** cases |
| Reason-code coverage | 49 typed error classes; **26** verification result codes with 26 distinct exit codes |
| E2E scenarios | **14 of 14 pass** |
| Concurrency tests | 9 races × 12 repeats, all pass |
| Fault-injection tests | 11 points, all pass |
| `test_epd2_crypto_1.py` | **32 passed** (was 30; the nine named provenance tests normalized, `test_epd2_crypto_1_source_file_path_present` added, `..._specification_sha256_present` split out from the upstream-digest check) |
| Reference-suite tests | **506 passed** |
| — `-m slow_conformance` | 15 passed, 491 deselected |
| Repository dependency guard | **9** tests (was 7), parsing `uv.lock` as TOML; every dual-state branch removed |
| Whole repository | **5 851 passed, 5 skipped, 0 failed**, with **no `--ignore`** |
| Line coverage | **90.9 %**, stdlib `trace` |
| Branch coverage | **NOT MEASURED** |

## 12. Assessments

**Canon.**

```text
CANON_VERSION remains 0.8.0.

No Canon domain, aggregate, event or invariant semantics changed.

Canon compatibility metadata continues to support
repository version 0.16.x.
```

`NO CANON CHANGE REQUIRED`. All eight §54 entities map onto aggregates
PACK-16A/16B/16C already specified. Ten implementation types — including
guardian records, threshold shares, checkpoint signer records and now the
signature provider — are held at service level on the PACK-12 / PACK-14 /
PACK-15 precedent. Swapping an implementation for a library is the clearest
possible case of a change invisible to canon: a signature that verifies
under the same key over the same bytes is the same signature whoever's
arithmetic produced it.

"Continues to support" rather than "was updated": the widening of
`repository_compatibility` to `<0.17.0` happened in the 0.16.0 round, is
correct, and is not reverted. **Neither correction modified any file under
`docs/canonical/`** — phrased that way rather than as "canon files
untouched", which would be false about the entry's history.

**FIR.** **This correction moved no FIR outcome at all.** It improved the
evidence behind three entries without changing any of their states.
`FIR-ROADMAP-006` reaches *implemented in reference form*,
partially, and keeps its register status `approved`. `FIR-INV-002` remains
*partially implemented* and is **not closed**. `FIR-ASM-006` / `FIR-ASM-007`
reach *test harness complete*. `FIR-TRUST-001` moves from *deferred* to
*partially implemented* — the signature half of the signature-and-timestamp
framework exists, the timestamp half does not. `FIR-SEC-002` stays *blocked
pending external review*, and the temptation to move it was subtler this
round than last: it is easy to read "we now use OpenSSL and the parameters
reconstruct offline" as partial assurance. It is not. Using a well-reviewed
library means somebody else's code was reviewed, which is a different
sentence from an external cryptographer reviewing this system. `FIR-ROADMAP-007`, `FIR-SEC-001` and
`FIR-OSS-006` are *deferred to PACK-17*. **New FIR IDs: none. Statuses
changed: none. None of the eight unclosable items was closed.**

**`VO-08`: OPEN.** Owned by PACK-16B external cryptographic review with
independent confirmation in PACK-17. Not closed, not narrowed, not re-owned.
No BSI conformity is claimed. It is named in the verifier's `NOT_CHECKED`
list, so every verification result — including a passing one — tells its
reader the parameters have not been assessed.

**Acceptance matrix.** 85 rows: 72 `SATISFIED`, 6 `PARTIALLY SATISFIED`,
2 `DEFERRED`, 4 `BLOCKED`, 1 `NOT APPLICABLE`. 72 + 6 + 2 + 4 + 1 = 85.
`CORRECTED` is not used as a status.

## 13. Open decisions

**Closed by this finalization: 2. Opened: 0. Still open: 9.** Both closures are
environmental, and neither is cryptographic.

```text
CLOSED BY THIS FINALIZATION
OD-P16D-16  DEPENDENCY LOCK: REGENERATED
            FROZEN CLEAN INSTALL: PASS on a network-enabled host
            cryptography 46.0.7 resolved in uv.lock with artefact hashes,
            inside the epd2-voting-service graph
OD-P16D-17  IMMUTABLE UPSTREAM IMPLEMENTATION PROVENANCE: RECORDED
            commit 520651138110a13f777409e96606454df928ceac,
            src/eg/src/standard_parameters.rs,
            sha256 ad38bfa68d31131a7d721e08d359224b21e967aae4d517534a60a109e10f5770

NARROWED, NOT CLOSED
OD-P16D-05  constant-time. STILL THE PRODUCTION BLOCKER

STILL OPEN
OD-P16D-02  no comparison against a COMPLETE independent implementation
OD-P16D-03  property tests are deterministic loops, not hypothesis
OD-P16D-04  concurrency evidence covers one in-memory store
OD-P16D-06  no cross-mirror split-view detection
OD-P16D-08  no production authentication
OD-P16D-10  the reference tally handles one ballot style
OD-P16D-11  the key ceremony has no custody model
OD-P16D-12  the signer registry's own authorisation is unverifiable

CLOSED EARLIER, STILL CLOSED
OD-P16D-01, -07, -09, -13, -14, -15
```

**Nothing was closed to make the round look finished, and the two that closed
did so on command output.** `OD-P16D-16` and `-17` had been re-attempted every
round and had failed every time, with verbatim transcripts kept rather than
summarised — which is exactly why running the same commands on a host with
access produced evidence a reviewer can compare line by line. `VO-08` remains
open, and every never-closed obligation — external cryptographic review, a
complete independent verifier, full ElectionGuard ecosystem interoperability,
constant-time production assurance, production HSM, production key custody,
production guardian ceremony, legal certification — is untouched. **A round that
clears two environmental blockers has cleared two environmental blockers.**

## 14. Residual risks and production blockers

```text
VERIFIED ELSEWHERE, NOT IN THE BUILD SESSION
  the frozen install ran on a network-enabled host; this session
    verified the lock's contents and the imported library's version
  the upstream file's digest was computed on that host; this session
    verified the pin's internal consistency and re-derived every
    parameter offline, but did not re-fetch the bytes
    -> one command settles it: curl -sL <pinned-url> | sha256sum

PRODUCTION BLOCKER
  no constant-time guarantee across three surfaces:
    guardian secret operations     secret-bearing, pure Python
    secret nonce use               secret-bearing, pure Python
    Ed25519 private-key signing    NARROWED - OpenSSL, unmeasured here
  (public verification carries no secret)

PRODUCTION PREREQUISITES
  VO-08 open; the parameters are present but not assessed
  no key custody: the ceremony runs in one process
  the signer registry's own authorisation is unverifiable
  no production authentication or credential integration
  no HSM or key-storage boundary
  no production data plane; concurrency proven only in memory
  no comparison against a complete independent implementation
  no external cryptographic review
  no legal assessment

FURTHER RESIDUALS
  a compiled native artefact (Rust bindings over libcrypto) is in the
    runtime path; its resolution is now hash-pinned in uv.lock, which
    fixes which bytes install and says nothing about how they behave;
    a libcrypto CVE remains an EPD2 concern
  no secret-material zeroization; Python cannot do it reliably
  no nonce-reuse detector
  is_probable_prime() is Miller-Rabin, not a proof
  branch coverage not measured
  the reference tally handles one ballot style
  no trusted timestamping
  role restriction and retention of audit evidence not implemented
```

## 15. Commands

**Executed in the build session, with output in
`PACK-16D-IMPLEMENTATION-REPORT.md` §3:**

```text
ruff check .                           All checks passed!
ruff format --check .                  498 files already formatted
mypy services/voting-service           Success: no issues found in 70 source files
pytest (whole repository, NO --ignore)  5851 passed, 5 skipped, 3 warnings (138.56 s)
pytest tests/reference/                506 passed (76.41 s)
pytest -m slow_conformance ...         15 passed, 491 deselected (9.82 s)
pytest -m "not slow_conformance" ...   491 passed, 15 deselected (71.32 s)
pytest tests/repository/test_pack16d_signature_dependency.py   9 passed
pytest test_epd2_crypto_1.py           32 passed in 29.54s
pytest test_guardians.py               28 passed in 3.10s
pytest test_checkpoint_signatures.py   44 passed in 0.79s
pytest test_conformance.py             19 passed in 5.84s
pytest test_target_conformance.py      15 passed in 9.00s
pytest test_concurrency.py             87 passed in 11.25s
pytest test_fault_injection.py         22 passed in 2.26s
pytest test_negative_corpus.py         41 passed in 2.30s
pytest test_casting_units.py           28 passed in 1.83s
pytest test_e2e.py                     24 passed in 4.60s
pytest test_verifier_branches.py       33 passed in 2.15s
pytest test_invariants.py              61 passed in 0.65s
pytest test_vectors.py                 31 passed in 1.44s
pytest test_crypto_units.py            24 passed in 4.58s
pytest test_property.py                17 passed in 7.45s
scripts/verify_versions.py             OK: all version sources are consistent.
scripts/check_canon_0_8_0.py           OK: all 18 canon 0.8.0 amendment checks passed.
scripts/check_repository.py            OK: all 983 required paths are present.
scripts/check_forbidden_files.py       OK: no forbidden paths found.
```

**Executed on the network-enabled host, not in the build session:**

```text
uv lock                                uv.lock 1a1e5a72...d543 -> b2d07754...8066
rm -rf .venv
uv sync --all-groups --frozen          Checked 61 packages
git clone / git log / git checkout /
  sha256sum on microsoft/electionguard-rust
                                       commit 520651138110a13f777409e96606454df928ceac
                                       src/eg/src/standard_parameters.rs
                                       sha256 ad38bfa6...5770
```

These are recorded as performed elsewhere rather than folded into the list
above, because the build session has no package index and no route to GitHub.
It verified their **outputs** — the lock parsed and checked field by field, the
pin checked for internal consistency, every parameter re-derived offline, and
the imported `cryptography` asserted version-identical to the locked
resolution — and it did not re-run them.

**Not executed, and not claimed as a PASS:**

```text
npm ci and every npm script    npm registry returns HTTP 403; the entire
                               Node and frontend side was not executed
hypothesis property tests      hypothesis not installable here
pytest --cov / branch coverage no coverage tool installable here
uv sync --all-groups --frozen  re-run in the build session: no package index
curl <pinned-url> | sha256sum  re-fetch of the upstream bytes: no route to
                               raw.githubusercontent.com from this session
```

The Node.js **conformance oracle** is unrelated to the npm side: a
standalone script run directly by the Node binary, needing no
`node_modules`.

`ruff`, `mypy` and `pytest` ran from a standalone toolchain rather than
through `uv run`, so their versions may differ from the pinned ones — `mypy`
reported 1.20.2, which matches. Reference-suite runs put the workspace `src`
directories **and the interpreter's site-packages** on `PYTHONPATH`; the
interpreter's `cryptography` is 46.0.7, which
`test_vetted_provider_imports_and_matches_the_lock` asserts equal to the
locked resolution.

### 15.1 The one command that closes the last verification gap

```bash
curl -sL https://raw.githubusercontent.com/microsoft/electionguard-rust/520651138110a13f777409e96606454df928ceac/src/eg/src/standard_parameters.rs | sha256sum
```

Expected: `ad38bfa68d31131a7d721e08d359224b21e967aae4d517534a60a109e10f5770`.
This is the only claim in the handover that rests on a value computed
elsewhere, and it takes one command on any networked machine to settle.
Everything else — the parameter values themselves included — is checkable
offline from this tree.

## 16. What the auditor should attack first

1. **The one value this tree cannot check itself.** `source_sha256` was
   computed on a network-enabled host. Run the command in §15.1 and compare.
   If it disagrees, the pin is wrong and everything resting on it needs
   re-examining — which is precisely why the artefact records the digest's
   verification scope instead of presenting it as first-hand.
2. **Whether `AM-79` and `AM-89` were promoted honestly.** The defect the
   previous audit found was a status contradicting its own evidence column,
   and the same error is possible pointing the other way — a row promoted
   because an obstacle disappeared rather than because its conditions were
   met. Check each of the ten conditions against the named test, then read
   the other 88 rows' evidence columns against their statuses. That is the
   check that caught the original defect.
3. **Whether the dependency tests still bite.** They were written to pass in
   both the blocked and the locked state while the blocker was open; every
   one of those branches has been removed. Delete the `cryptography` block
   from `uv.lock` and confirm the suite goes red — if it does not, the
   accommodation outlived its cause.
4. **The parameter reconstruction.** This is still what the constants
   actually rest on, pin or no pin. Recompute `ln 2` independently and
   rebuild `p`; then check the specification PDF, whose digest is inherited
   from PACK-16B and was not re-verified here.
5. **What the RFC vectors do not cover.** Three of RFC 8032's vectors are
   reproduced, and the OpenSSL CLI shares an upstream with the provider it
   checks.
6. **The Node oracle's independence.** Strongest conformance evidence in the
   round, same author as the producer, written from the written grammar.
7. **The ceremony's threat model** (`OD-P16D-11`) and **the signer registry**
   (`OD-P16D-12`).
8. **The five remaining skips.** An earlier round found a contract test that
   had been skipping rather than passing and was hiding a real mismatch.

## 17. Stop condition

The archive is built and work has stopped. **PACK-17 is not started and must
not start before independent acceptance of PACK-16D.** No part of this round
may be treated as production acceptance, external review, certification or
legal activation.

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
