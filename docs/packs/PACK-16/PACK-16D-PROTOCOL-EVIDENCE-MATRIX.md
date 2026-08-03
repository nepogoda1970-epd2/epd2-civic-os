# PACK-16D — Protocol Evidence Matrix

**Round:** PACK-16D — Network-Enabled Finalization: Lockfile Regeneration,
Immutable ElectionGuard Provenance and Final Acceptance Alignment.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 0. This document is the single canonical PACK-16D Evidence Registry

> **All PACK-16D Evidence IDs are canonically defined in
> `PACK-16D-PROTOCOL-EVIDENCE-MATRIX.md`.**

The three earlier rounds keep their own registries and namespaces:

```text
PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md    E-*
PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md    F-*
PACK-16C-PROTOCOL-EVIDENCE-MATRIX.md    G-*
PACK-16D-PROTOCOL-EVIDENCE-MATRIX.md    H-*   (this file)
```

**PACK-16D defines no `E-*`, `F-*` or `G-*` identifier, redefines none, and
retires none.** Where this round rests on an earlier round's source it cites
that round's ID as inherited (§3) rather than minting a duplicate — the same
source under two IDs is how a registry starts disagreeing with itself. There
is exactly one deliberate overlap this round, `H-08`, and `H-R09` records
why it was accepted rather than leaving it to be discovered.

**This is not a second registry.** `PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md`
carries the round's `EC-*` **rules and comparison narrative**; the sources
those rules rest on are defined here and nowhere else. If the two ever
disagree about a source, this file is right and that one is a defect.

### 0.1 Rules of the registry

```text
One definition per Evidence ID. A mention is not a definition.
An ID is defined here or it does not exist.
An ID is never reused for a different source.
A claim marked INF may not be presented as a source's statement.
A source that was not read is never cited as if it had been.
A tool's own output is evidence about the tool, not about a specification.
Marketing material is not evidence and appears in no entry.
A digest that names the wrong byte stream is withdrawn, never relabelled.
```

### 0.2 Kinds

```text
P  protocol or standards text        an external specification
X  cross-implementation              an independent implementation's output
S  source artefact                   a published implementation's source code
INF inference by this round          reasoning, never quoted as a source
```

## 1. Registry summary

| Kind | Count | IDs |
| --- | --- | --- |
| `P` protocol / standards text | 3 | `H-02`, `H-06`, `H-08` |
| `S` source artefact | 2 | `H-01`, `H-10` |
| `X` cross-implementation | 3 | `H-03`, `H-04`, `H-05` |
| `INF` inference | 2 | `H-07`, `H-09` |
| **Total** | **10** | `H-01` … `H-10`, contiguous |

**Added by this correction:** `H-08` (the specification, as the authoritative
parameter reference), `H-09` (the offline reconstruction of the parameter
set), `H-10` (`cryptography`, the vetted signature provider now in the
runtime path). **Rewritten in place:** `H-01` (its digest was withdrawn and
its role demoted to corroborating), `H-02` (the implementation it describes
was replaced), `H-03` (a different OpenSSL oracle), `H-04` (oracle version 2
and target-profile coverage), `H-05` (a new catalogue version and count).
**Retired: none. Renumbered: none. Reused: none.**

**The previous round's claim "sources cited but not read this round: 0" no
longer holds and has been removed rather than carried.** Two entries —
`H-01` and `H-08` — name external documents that **could not be retrieved in
this environment**, because `github.com`, `api.github.com` and the CDN
mirrors are all refused by the egress proxy with HTTP 403. Both say so in
their own text, neither carries a digest obtained here, and `H-08`'s digest
is explicitly inherited from PACK-16B. §4 counts them.

## 2. The registry

---

##### `H-01` · The ElectionGuard 2.1 baseline parameters as published Rust source — corroborating only — Kind `S`

- **Source title:** `microsoft/electionguard-rust` — `src/eg/src/standard_parameters.rs`
- **Institution / author:** Microsoft
- **Version / date:** **no version is pinned.** No commit SHA and no
  byte-exact digest of this file could be obtained in this environment. The
  file states that it implements the *ElectionGuard Design Specification
  v2.1.0*, §3.1.1 p. 14, "Standard Baseline Cryptographic Parameters"
- **Source type:** published reference-implementation source code
- **Stable reference:**
  `https://raw.githubusercontent.com/microsoft/electionguard-rust/520651138110a13f777409e96606454df928ceac/src/eg/src/standard_parameters.rs`
  — a **commit-pinned** raw URL, immutable by construction. SHA-256 of the
  file's raw bytes at that commit:
  `ad38bfa68d31131a7d721e08d359224b21e967aae4d517534a60a109e10f5770`.
  The `/main/` location survives in the profile artefact as a
  `NON-AUTHORITATIVE NAVIGATION URL` with
  `human_readable_url_is_authoritative: false` — now that a pinned URL sits
  beside it, it is the one a hurried reader is most likely to copy, so the
  marking matters more than it did before, not less. Licence: MIT (upstream
  repository)
- **Relevant section / path:** the four constants `p`, `q`, `g`, `r`
- **Property supported:** **corroboration, not authority.** It is a second
  published place the same four constants appear, and it is the place a
  reader can most easily look at them. It is not what establishes them
- **Scope:** demoted this round. The authoritative reference for the
  parameter set is `H-08`, the specification; the values themselves are
  established without reference to any file by `H-09`, the offline
  reconstruction. `OD-P16D-01` stays closed on that basis and not on this
  entry's
- **Limitations, stated plainly because they are the whole entry:**
  - **The digest this entry previously carried — `3afa2962…` — is
    WITHDRAWN.** It was computed over a markdown rendering of the file
    rather than over the file's raw bytes, so it attested something other
    than what a reader would reasonably have taken it to attest. It is
    withdrawn rather than relabelled: a digest naming the wrong byte stream
    is worse than no digest, because it invites exactly the check it cannot
    survive. **No `H-*` entry records a `source_sha256` for this file**
  - **Now commit-pinned.** For two rounds this file could not be pinned: four
    access paths were refused by two distinct mechanisms, and rather than
    invent a hash the artefact carried explicit `null`s with a stated reason.
    The pin was obtained on a network-enabled host and is recorded as
    **commit `520651138110a13f777409e96606454df928ceac`** (2025-02-02),
    path `src/eg/src/standard_parameters.rs`, raw URL
    `https://raw.githubusercontent.com/microsoft/electionguard-rust/520651138110a13f777409e96606454df928ceac/src/eg/src/standard_parameters.rs`,
    **SHA-256 `ad38bfa68d31131a7d721e08d359224b21e967aae4d517534a60a109e10f5770`**,
    retrieved 2026-08-03. `unpinned_reason` and `auditor_action` were removed
    in the same change, which a test enforces. That closes `OD-P16D-17` and
    is why `AM-79` is `SATISFIED`
  - **The digest's verification scope is recorded rather than assumed.** It
    was computed on the network-enabled host; the build session verified the
    pin's internal consistency and re-derived every parameter offline but did
    **not** re-fetch the bytes. `source_sha256_verification_scope` in the
    artefact says exactly that, and names the one command that closes it:
    `curl -sL <pinned-url> | sha256sum`
  - It is an **implementation of** the specification, not the specification.
    The specification is `H-08` / `F-01` / `F-02`. An auditor checking the
    transcription should check it against the specification, not against
    this file
  - The values were transcribed by automated fetch and **not re-read by a
    second human**
  - The transcription is nevertheless verified by arithmetic that no
    single-digit error survives — `q = 2²⁵⁶ − 189`, `q | p−1`, `p = qr + 1`,
    `1 < g < p`, `g^q = 1 mod p`, `p`, `q` and `r/2` probable prime, `p`'s
    leading and trailing 256 bits all ones, and 3306 of 3584 middle bits
    equal to `ln 2` — and, since this correction, by full offline
    reconstruction (`H-09`), which depends on no file and no network at all
- **Documents / tests using evidence:** `PACK-16D-PARAMETER-PROFILE-IMPLEMENTATION.md` · `PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md` `EC-19`…`EC-31` · `ADR-102` · `tests/reference/test_epd2_crypto_1.py`
- **Classification:** `S` (corroborating)

##### `H-02` · RFC 8032 — the checkpoint signature scheme, normatively — Kind `P`

- **Source title:** *Edwards-Curve Digital Signature Algorithm (EdDSA)*
- **Institution / author:** S. Josefsson, I. Liusvaara — IRTF CFRG
- **Version / date:** RFC 8032, January 2017, Informational
- **Source type:** published standards-track-adjacent specification (IRTF stream)
- **Stable reference:** `https://www.rfc-editor.org/rfc/rfc8032`
- **Relevant section / page:** §5.1 (Ed25519 PureEdDSA: key generation, signing, verification, the `S < L` requirement); §7.1 (test vectors)
- **Property supported:** the scheme the vetted provider is configured for —
  `SIGNATURE_PROFILE = "Ed25519 (RFC 8032, PureEdDSA, SHA-512)"` in
  `crypto/signature_provider.py` — and **three** published §7.1 test vectors
  (TEST 1, the empty message; TEST 2, one byte; TEST 3, two bytes), each
  reproduced verbatim in `test_checkpoint_signatures.py` with its secret
  key, public key, message and signature, and each executed against the
  provider in this environment
- **Scope:** **this is now the primary conformance evidence for the
  signature primitive.** It is the only Ed25519 evidence in this round that
  does not share an upstream with the provider: `H-03` compares an OpenSSL
  CLI against a library that is also OpenSSL, and `H-10` is the provider
  itself. An externally published vector reproduced by the provider is the
  claim that survives that observation
- **Limitations:**
  - **Three of the RFC's vectors are reproduced, not all of them.** The
    RFC's longer messages, the 1024-byte vector and the Ed25519ph variant
    are not covered
  - RFC 8032 specifies **correctness, not side-channel resistance.** This
    entry says nothing about timing behaviour, and `OD-P16D-05` is not
    narrowed by it
  - This entry no longer describes an EPD² implementation of the scheme.
    `crypto/ed25519.py` was **deleted** by this correction; what the vectors
    are checked against is `H-10`
- **Documents / tests using evidence:** `PACK-16D-CHECKPOINT-SIGNATURE-AND-SIGNER-TRUST-MODEL.md` · `PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md` `EC-32`…`EC-39` · `ADR-102` · `tests/reference/test_checkpoint_signatures.py::test_rfc8032_vectors`
- **Classification:** `P`

##### `H-03` · The OpenSSL command-line tool, as a corroborating Ed25519 oracle — Kind `X`

- **Source title:** the `openssl` binary — `openssl pkeyutl -verify -rawin`
- **Institution / author:** the OpenSSL Project
- **Version / date:** **OpenSSL 3.0.13 (30 January 2024)**, as reported by
  `openssl version` and recorded in the oracle's own verdict; executed
  2026-08-02
- **Source type:** independent implementation, executed out-of-process
- **Stable reference:** driven by `tests/reference/crossimpl/openssl_cli_ed25519_oracle.py`, `ORACLE_VERSION = "openssl-cli-ed25519-1"`
- **Property supported:** six cases — the three RFC 8032 §7.1 vectors
  accepted, and three mutated-message variants of them rejected. The oracle
  imports **no** cryptographic Python library at all: a raw 32-byte public
  key is wrapped by hand in its twelve fixed RFC 8410 §4 SubjectPublicKeyInfo
  DER prefix bytes and handed to the tool through a file, and the tool
  answers with an exit code
- **Scope:** corroboration of the primitive. It establishes that a
  separately built, separately versioned artefact reached the same verdict
  on the same bytes, through a different execution path
- **Limitations, and the first is the reason this entry is no longer the
  strong one:**
  - **The CLI binary and the library the provider links share an upstream
    project.** `cryptography` links libcrypto in-process; the `openssl`
    binary is libcrypto with a command-line front end. A defect in OpenSSL's
    Ed25519 that survived across both builds would be invisible to this
    comparison. **This is the honest weak point of the round's signature
    evidence**, and the evidence that does *not* share a lineage is `H-02`
  - **This entry replaced an in-process oracle that was deleted, not
    retired quietly.** The previous round's
    `tests/reference/crossimpl/openssl_ed25519_oracle.py` called OpenSSL
    through `python-cryptography`. When the primitive was hand-written that
    was a genuine cross-implementation comparison. Once `cryptography`
    became the *provider*, the same script was comparing a library against
    itself in one process — agreement by construction. It was deleted rather
    than kept, because a cross-check that cannot disagree is not evidence
  - **Empty messages are reported `skipped`, never passed.** `openssl
    pkeyutl -rawin` refuses a zero-length input file; that is a tool
    limitation, not a verification result, and the oracle says so with a
    reason. TEST 1 is covered by `H-02` directly instead
  - Both sides follow RFC 8032. Agreement rules out an implementation error
    against that specification; it does not rule out a defect in the
    specification
- **Documents / tests using evidence:** `PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md` `EC-40`…`EC-45` · `PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md` `LD-36`, `LD-37` · `tests/reference/test_checkpoint_signatures.py`
- **Classification:** `X`

##### `H-04` · The independent Node.js verifier — Kind `X`

- **Source title:** `tests/reference/crossimpl/independent_verifier.mjs` — an independent re-derivation of EPD²'s own protocol arithmetic
- **Institution / author:** **EPD² — this round's own work**, written from the *written grammar and specification documents* rather than from the Python implementation
- **Version / date:** `oracle_version = "epd2-independent-verifier-2"`, executed 2026-08-02 under Node.js
- **Source type:** cross-implementation oracle, executed
- **Stable reference:** in-repository at the path above, 521 lines, importing only `node:` builtins
- **Property supported:** independent agreement on **all twelve
  target-profile core operations, on `EPD2-CRYPTO-1` itself** — parameter
  digest, group element encoding, scalar encoding, selection encryption,
  selection proof, ballot hash, confirmation code, accumulation, guardian
  public commitment, decryption share, 3-of-5 threshold combination and
  aggregate tally recovery — plus the earlier test-profile comparisons,
  which are kept rather than discarded. Version 2 added the
  `scalar_encoding`, `guardian_commitment` and `ballot_structural` handlers
- **Scope:** the only evidence in this round capable of catching an error
  the Python implementation makes *consistently* — and it caught one. See
  `H-07`. Two properties of version 2 carry most of its weight:
  - **Every result now carries a machine-readable envelope**: `vector_id`,
    `operation`, `profile_id`, `expected`, `actual`, `match` and
    `oracle_version`. A verdict is evidence a re-audit can diff, not prose a
    human has to interpret
  - **`ballot_structural` is handed the ballot's *fields* and rebuilds the
    canonical bytes itself** before hashing them. Handing the oracle the
    producer's canonical encoding would test the hash function and not the
    encoding — and the encoding is exactly where the previous round's real
    defect was
- **Limitations, stated because they are the entry's weakest point:**
  - **Same author as the code it checks.** It re-derives from the grammar
    and it found a real defect, which is some evidence of genuine
    independence — but shared assumptions are precisely what a shared author
    cannot see. `PACK-16D-HANDOVER.md` §16 asks an auditor to attack this
    specifically
  - It implements the operations EPD² needs, not a complete ElectionGuard
    implementation. `OD-P16D-02` stays open for that reason
  - The test-profile comparisons remain test-profile comparisons. They are
    counted separately from the target-profile ones in the catalogue
    (`EvidenceClass` has distinct members for each) rather than merged into
    one number
  - Two deliberately invalid target-profile fixtures are fed to it to prove
    it can fail. An oracle that has never been observed to fail is not
    evidence
- **Documents / tests using evidence:** `PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md` `EC-46`…`EC-63` and its target-profile section · `tests/reference/test_conformance.py` · `tests/reference/test_target_conformance.py`
- **Classification:** `X`

##### `H-05` · The committed conformance catalogue — Kind `X`

- **Source title:** `services/voting-service/tests/reference/vectors/PACK-16D-CONFORMANCE-EVIDENCE.json`
- **Institution / author:** EPD² — this round
- **Version / date:** catalogue version **`EPD2-CONFORMANCE-2`**, generated 2026-08-02
- **Source type:** committed comparison record
- **Stable reference:** in-repository at the path above
- **Property supported:** **26 entries**, classified across the five members
  of `EvidenceClass`:

  ```text
  internal-stability                    0   (deliberately - never promoted here)
  primary-source                        1
  rfc-conformance                       1
  cross-implementation-test-profile     8
  cross-implementation-target-profile  16
  ```

  Each entry carries its evidence class, operation, profile, source title,
  version, location, digest, retrieval date, licence, canonical input,
  expected output, comparison result and limitations.
  `PRIMARY_SOURCE_UNAVAILABLE` names six operations with no published
  external vector, each with a reason
- **Scope:** the machine-readable record behind every conformance claim in
  this round, and the artefact a re-audit should diff first. The
  `internal-stability` count of zero is the structural half of the
  classification: those vectors are not merely labelled differently, they
  live in a different file
- **Limitations:**
  - It is a **record of comparisons**, not itself an external source. Its
    weight is entirely `H-01`…`H-04`'s and `H-08`…`H-10`'s
  - The 23 internal-stability vectors are **excluded** from it by design and
    keep their `stability-only (interoperability NOT established)` status. A
    test fails if a self-generated vector is ever relabelled as conformance
    evidence
  - Entry `CV-01`'s `source_location` and `source_digest` fields still name
    the `/main/` URL and the withdrawn `3afa2962…` digest. **The profile
    artefact, not the catalogue, is the provenance of record** — see `H-08`
    and `H-01` — and this divergence is stated here rather than left for a
    reader to trip over
- **Documents / tests using evidence:** `PACK-16D-TEST-VECTOR-CATALOG.md` · `PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md` · `tests/reference/test_conformance.py::test_conformance_evidence_catalogue_is_committed_and_classified`
- **Classification:** `X`

##### `H-06` · No published vector exists for six EPD²-specific operations — Kind `P` (negative finding)

- **Source title:** *ElectionGuard Design Specification* v2.1.0, and the absence of any accompanying worked-example corpus
- **Institution / author:** Microsoft Research; searched 2026-08-02
- **Source type:** negative finding against a protocol specification
- **Stable reference:** as `F-01`; the finding is the absence of a published artefact
- **Property supported:** for `selection_encryption`, `selection_proof`, `ballot_hash`, `confirmation_code`, `accumulation` and `threshold_tally`, **no external primary-source vector was located.** The specification gives equations, not examples with fixed randomness; and four of the six are EPD² constructions — the canonical encoding `EPD2-ENC-1`, the domain-separation registry, the confirmation-code alphabet and EPD²'s Fiat–Shamir context — which by construction have no external counterpart
- **Scope:** the reason `primary-source conformance vectors` is **`PARTIALLY SATISFIED`** in the acceptance matrix and not `SATISFIED`. Those six operations are covered by `H-04` instead, and the substitution is named rather than hidden
- **Limitations:**
  - **An absence of evidence found is not proof of absence.** A vector corpus may exist somewhere this round did not look; the finding is that none was located, not that none exists
  - The finding is recorded in code (`PRIMARY_SOURCE_UNAVAILABLE`) with a per-operation reason, and a test asserts it is declared rather than silently empty
  - Cross-implementation coverage of those six operations is now on the
    target profile as well as the test profile (`H-04`). That widens the
    substitute; it does not turn it into a primary source
- **Documents / tests using evidence:** `PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md` §9 · `PACK-16D-ACCEPTANCE-MATRIX.md` row 82 · `tests/reference/test_conformance.py::test_primary_source_unavailability_is_declared_not_hidden`
- **Classification:** `P` (negative finding)

##### `H-07` · The canonical-encoding ambiguity, and what it demonstrates — Kind `INF`

- **Source title:** no external source — inference by this round from `H-04`'s output
- **Institution / author:** EPD² — this round
- **Version / date:** 2026-08-02
- **Source type:** inference
- **Property supported:** `encode_seq` concatenated its items raw after a count, so `SEQ([b"ab", b"c"])` and `SEQ([b"a", b"bc"])` produced identical bytes — two different sequences sharing a digest, in a function every protocol digest runs through. `encode_struct` appended field values raw for the same reason. Both now length-prefix every member
- **Scope:** the round's strongest argument that the audit's `EXTERNAL CONFORMANCE: FAIL` was correct. The defect was invisible to 23 self-generated stability vectors — they encoded and decoded it consistently — and became visible the moment an implementation written from the *grammar* was asked to agree. It is also why `H-04`'s `ballot_structural` handler rebuilds the canonical bytes from fields rather than accepting the producer's encoding
- **Limitations:**
  - **This is an inference, not a source's statement.** No external party has confirmed the analysis, and it must never be quoted as though one had
  - One defect found is not a measure of how many remain
  - Every digest in the round changed as a consequence, which the stability vectors did catch — that is the one thing they are for
- **Documents / tests using evidence:** `ADR-102` *Context* and *Canonical encoding* · `PACK-16D-IMPLEMENTATION-REPORT.md` §7 · `PACK-16D-CANONICAL-ENCODING-SPECIFICATION.md` · `tests/reference/test_negative_corpus.py::test_neg_ambiguous_sequence_encoding`
- **Classification:** `INF`

##### `H-08` · The ElectionGuard Design Specification, as the authoritative parameter reference — Kind `P`

- **Source title:** *ElectionGuard Design Specification*
- **Institution / author:** Josh Benaloh, Michael Naehrig, Olivier Pereira — Microsoft Research
- **Version / date:** **2.1.0**
- **Source type:** official protocol specification — a released document, not a branch
- **Stable reference:**
  `https://github.com/microsoft/electionguard/releases/download/v2.1/EG_Spec_2_1.pdf`
  — a **versioned release asset under the tag `v2.1`**, which is the
  property that matters here: it is not a `/main/` path and it does not
  change under a reader. SHA-256
  `a263ab3cd2cf28f05de324ecd2d9752ffed45f814709582b4c2bb23d1826b936`
- **Relevant section / page:** §3.1.1, page 14 — "Standard Baseline Cryptographic Parameters"
- **Property supported:** the **authoritative** provenance of
  `EPD2-CRYPTO-1`. `crypto/profiles/EPD2-CRYPTO-1.json` now carries this
  document under `source.authoritative` with `kind: "specification"`, and
  the Rust file (`H-01`) under `source.corroborating` with
  `human_readable_url_is_authoritative: false`. The round's provenance claim
  rests on a specification and a derivation, not on a branch
- **Scope:** closes the audit's `PARAMETER SOURCE REPRODUCIBILITY: PARTIAL —
  MUTABLE URL` half, together with `H-09`. `OD-P16D-14` is closed on this
  entry and `H-09`; `OD-P16D-17` is closed on `H-01`'s commit pin. Pinning the
  implementation source does **not** make it normative — the specification
  here remains the authoritative reference and `H-01` remains corroborating
- **Limitations — the important one first:**
  - **The digest above is INHERITED from PACK-16B evidence `F-01` and was
    NOT re-verified this round.** It was recorded first-hand there, over an
    813 495-byte document. **This round did not retrieve the PDF**: the
    release asset is served from `github.com`, which this environment's
    egress proxy refuses with HTTP 403. The artefact says so in
    `document_sha256_provenance`, and this entry says so here. Anyone
    treating the digest as re-attested by PACK-16D is reading a claim that
    is not made
  - **This entry names the same document as `F-01` and `F-02`**, which
    `H-R07` would normally forbid. `H-R09` records why the overlap was
    accepted and what it is not permitted to become
  - Having the specification is not having an assessment of it. `VO-08` is
    **OPEN**, no BSI conformity is claimed, and the artefact carries
    `specification_review_status: "VO-08 OPEN"` so the gap travels with the
    parameters
- **Documents / tests using evidence:** `PACK-16D-PARAMETER-PROFILE-IMPLEMENTATION.md` · `PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md` `EC-19`…`EC-31` · `ADR-102` *Parameter profile* · `crypto/profiles/EPD2-CRYPTO-1.json`
- **Classification:** `P`

##### `H-09` · The parameter set reconstructed offline from the published rule — Kind `INF`

- **Source title:** no external source — inference and computation by this round
- **Institution / author:** EPD² — this round
- **Version / date:** 2026-08-02
- **Source type:** inference, computed locally with no file and no network
- **Property supported:** the whole `EPD2-CRYPTO-1` parameter set is
  **rebuilt from the published structural rule**, recorded in the artefact's
  new `derivation` block:

  ```text
  p          = ONES(256) || M(3584) || ONES(256)
  M          = (first 3305 fractional bits of ln 2) << 279 | delta_low
  delta_low  = 0x445744fb5f2da4b751005892d356890defe9cad9b9d4b713e06162a2d8fdd0df2fd608   (279 bits)
  q          = 2**256 - 189
  r          = (p - 1) // q
  g          = pow(2, r, p)
  ```

  `ln 2` is **computed locally as `2*atanh(1/3)`**, summed as
  `2 * Σ_{k≥0} (1/3)^(2k+1)/(2k+1)` — not read from a table and not
  fetched. All four constants reconstruct exactly, and the artefact records
  `p_reconstructs_from_ln2_rule_and_delta`, `g_equals_2_pow_r_mod_p` and
  `r_equals_p_minus_1_over_q` as verified
- **Scope:** **this is the strongest provenance evidence in the round, and
  it is the one that needs no network at all.** A URL says where bytes came
  from; a derivation says the bytes are the ones the published rule
  produces. A transcription error anywhere in `p`, `q`, `g` or `r` fails
  reconstruction, so the parameter values survive the fact that `H-01` has
  no commit pin and `H-08` could not be retrieved here.
  `parameter_digest = f0af5b71412ccf93a1eaf93364c223f5339cdb2815a2efcfa1bd775cd2bf17fb`
  is unchanged by the restructuring
- **Limitations:**
  - **This is an inference by this round, not a source's statement.** No
    external party has confirmed that this reconstruction is the rule the
    specification intends; it is EPD²'s reading of the documented structure,
    and it must never be quoted as though Microsoft Research had attested it
  - It establishes that the constants are **internally the ones the rule
    produces**. It does not establish that the rule is the right rule, that
    the group is appropriate for a binding German election (`VO-08`, OPEN),
    or that 279 bits of `delta_low` were themselves derived rather than
    chosen upstream — `delta_low` is recorded, not derived
  - `is_probable_prime()` is Miller–Rabin over 24 small-prime bases, not a
    proof of primality
- **Documents / tests using evidence:** `PACK-16D-PARAMETER-PROFILE-IMPLEMENTATION.md` · `ADR-102` *Parameter profile* · `crypto/profiles/EPD2-CRYPTO-1.json` `derivation` · `tests/reference/test_epd2_crypto_1.py`
- **Classification:** `INF`

##### `H-10` · `cryptography`, the vetted signature provider now in the runtime path — Kind `S`

- **Source title:** `cryptography` (Python Cryptographic Authority), backed by OpenSSL's libcrypto
- **Institution / author:** Python Cryptographic Authority; the OpenSSL Project
- **Version / date:** declared as `cryptography>=46.0.7,<47` in `services/voting-service/pyproject.toml` and **resolved in `uv.lock` as 46.0.7** from `https://pypi.org/simple`, with `cffi 2.1.0` and `pycparser 3.0`. The library the test suite imports is linked against **OpenSSL 3.5.6 (7 April 2026)** and its version is asserted equal to the locked one, which ties the exercised code to the recorded resolution
- **Source type:** published, widely deployed implementation, executed as a runtime dependency
- **Stable reference:** `https://github.com/pyca/cryptography` · `https://cryptography.io/` · Licence **Apache-2.0 / BSD-3-Clause**, at the user's option
- **Property supported:** every checkpoint signature and every checkpoint
  signature verification in the round. `crypto/signature_provider.py` is a
  **port, not an implementation**: `CheckpointSignatureProvider` is a
  `@runtime_checkable` Protocol with six operations
  (`generate_test_keypair`, `load_public_key`, `sign_checkpoint`,
  `verify_checkpoint`, `public_key_bytes`, `signature_bytes`), and
  `CryptographyEd25519Provider` is the single active implementation, with
  `profile = "Ed25519 (RFC 8032, PureEdDSA, SHA-512)"` and
  `backend = "cryptography (OpenSSL Ed25519)"`. Six library calls, all in
  that one module
- **Scope:** closes `OD-P16D-13`, the audit's `CHECKPOINT SIGNATURE
  PRIMITIVE POLICY: FAIL — HANDWRITTEN ED25519`. `crypto/ed25519.py` is
  **deleted**, not deprecated and not relocated, and an `ast` test asserts
  no module under `reference/` imports a hand-written `ed25519` module or
  imports `cryptography` outside the provider
- **Limitations:**
  - **The frozen install was executed elsewhere.** `uv lock` and
    `rm -rf .venv && uv sync --all-groups --frozen` (`Checked 61 packages`)
    ran on a network-enabled host; the build session that produced this
    candidate still has no package index and did not re-run them. What that
    session verifies is the lock's parsed contents — registry source,
    `sha256:` hashes on all 43 artefacts, both transitives, membership of the
    `epd2-voting-service` graph — and the imported library's version. "The
    tests are green" and "the frozen install passes" stay two claims.
    `OD-P16D-16` is closed on the recorded command output, not on the tests
  - **A compiled native artefact is now in the runtime path.**
    `cryptography` links a Rust binding layer over libcrypto; the wheel is
    platform-specific. That is a real supply-chain consideration and is not
    minimised
  - **No constant-time claim is made by EPD².** OpenSSL pursues
    side-channel resistance as a design goal for Ed25519, which is a
    materially better position than a hand-written double-and-add — but a
    library's own design goals are not this repository's evidence, EPD² has
    measured nothing, and `OD-P16D-05` stays open
  - **A tool's output is evidence about the tool.** That the provider agrees
    with RFC 8032's vectors is `H-02`'s claim, not this entry's
- **Documents / tests using evidence:** `PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md` §2.1, §4 · `PACK-16D-CHECKPOINT-SIGNATURE-AND-SIGNER-TRUST-MODEL.md` · `PACK-16D-SECURITY-AND-SIDE-CHANNEL-LIMITATIONS.md` §4 · `ADR-102` *Dependency decision*, *Checkpoint authenticity* · `tests/reference/test_checkpoint_signatures.py` · `tests/repository/test_pack16d_signature_dependency.py`
- **Classification:** `S`

## 3. Inherited evidence this round relies on and does not redefine

| Inherited ID | Round | Source | What this round uses it for |
| --- | --- | --- | --- |
| `E-19`, `E-22` | PACK-16A | the weak-Fiat–Shamir failure class | why every challenge binds the statement and the context |
| `F-01` | PACK-16B | *ElectionGuard Design Specification* v2.1.0 §3.1.1, PDF digest `a263ab3c…b936` | the digest `H-08` carries. **PACK-16B read that document first-hand; this round did not**, and `H-08` inherits the digest rather than re-attesting it |
| `F-02` | PACK-16B | the same specification, §3.1 parameter derivation | the documented `r/2`-prime and `ln 2` structure that `H-09` reconstructs from and that `H-01`'s arithmetic check tests for |
| `F-08` | PACK-16B | strong Fiat–Shamir in all three proof families | the proof transcripts the Node.js oracle re-derives |
| `F-15`, and its counterweight | PACK-16B | Pedersen-DKG bias, and the paper showing it survivable for discrete-log schemes | why the ceremony publishes coefficient commitments and a proof of possession, and why `2k ≤ n` is refused |
| `G-01` … `G-05` | PACK-16C | RFC 9162 §11.3, RFC 6962 §5, `draft-ietf-trans-gossip-05`, C2SP `tlog-witness`, and the inference from them | why cross-mirror split-view detection is still unimplemented (`OD-P16D-06`) even now that checkpoints are signed |
| `G-02` | PACK-16C | RFC 6962 | the Merkle tree, inclusion and consistency proof shapes |

## 4. Integrity block — computed, not asserted

```text
canonical PACK-16D evidence registries ............ 1    (this file)
substantive PACK-16D definitions .................. 10   H-01 … H-10
  executed or measured in this environment ........ 5    H-02, H-03, H-04, H-05, H-10
  inference (INF) ................................. 2    H-07, H-09
  negative findings ............................... 1    H-06
  cited without a first-hand digest this round .... 2    H-01, H-08
IDs added by this correction ...................... 3    H-08, H-09, H-10
IDs rewritten in place ............................ 5    H-01, H-02, H-03, H-04, H-05
IDs renumbered .................................... 0
IDs reused for a different source ................. 0
IDs retired ....................................... 0
reserved IDs ...................................... 0
duplicate definitions ............................. 0
conflicting definitions ........................... 0
IDs defined outside this file ..................... 0
E-*, F-* or G-* identifiers defined here .......... 0
E-*, F-* or G-* identifiers redefined here ........ 0
inherited entries cited in §3 ..................... 7
digests withdrawn this round ...................... 1    H-01's 3afa2962…
digests inherited and not re-verified this round .. 1    H-08's a263ab3c…
same-document overlaps with an earlier round ...... 1    H-08 / F-01, F-02  (see H-R09)
```

The five counted as **executed or measured in this environment** are:
`H-02`'s three §7.1 vectors, run against the provider; `H-03`'s oracle, run
against the `openssl` binary; `H-04`'s oracle, run against the exported
fixtures; `H-05`'s catalogue, generated and asserted; and `H-10`'s version
and backend, read from the installed library. The two counted as **cited
without a first-hand digest** name documents this environment could not
retrieve, and say so in their own text.

| ID | Rule |
| -- | ---- |
| `H-R01` | **This registry no longer claims "sources cited but not read = 0", because it would be false.** Two entries name documents that could not be retrieved here, and both say so: `H-01` carries no digest at all after `3afa2962…` was withdrawn, and `H-08` carries a digest inherited from `F-01`. A registry that quietly kept the old count would be the exact defect this file exists to prevent |
| `H-R02` | **A tool's output is evidence about the tool.** `H-03` establishes that the provider and the `openssl` binary agree; it establishes nothing about whether RFC 8032 is the right choice, which is a decision, not a fact — and, since both are OpenSSL underneath, rather less about the primitive than the same comparison established last round |
| `H-R03` | **`H-07` and `H-09` are inferences and are marked as such.** They may be cited for what this round observed and computed; they may never be presented as an external party's finding. `H-09` in particular is EPD²'s reading of a published structural rule, not a statement by its authors |
| `H-R09` | **`H-08` is the registry's one same-document overlap with an earlier round, and it is deliberate.** `H-R07` forbids re-minting an inherited source, and the rule is right. The exception is admitted because the *property supported* is new: PACK-16B cited the specification for the subgroup order and the derivation; this round cites it as the **authoritative provenance field of a committed artefact**, a role that did not exist before. `H-08` is bounded by two conditions — it re-attests nothing, and its digest is explicitly `F-01`'s. If a future round finds `H-08` making a first-hand claim about that PDF, the entry is wrong, not the rule |

## 5. What this evidence does **not** establish

```text
that EPD2-CRYPTO-1 is appropriate for a binding German election  -> VO-08, OPEN
that any of this is constant-time or side-channel resistant      -> OD-P16D-05
that a complete independent implementation agrees with this one  -> OD-P16D-02
that the key ceremony is a ceremony rather than a demonstration  -> OD-P16D-11
that the signer registry a verifier is handed is the right one   -> OD-P16D-12
that a frozen install was performed in this build session        -> executed
                                                                    on the
                                                                    network-
                                                                    enabled host
that the upstream file's bytes were re-fetched here              -> pinned and
                                                                    digest
                                                                    recorded;
                                                                    not re-
                                                                    fetched
that an external cryptographer reviewed anything                 -> never this round
```

`H-R04` — **A vetted provider, an authoritative specification reference, an
offline reconstruction and twelve target-profile cross-checks are a real
improvement over two oracles and a branch URL, and they are still not
interoperability.** The distance between them is `OD-P16D-02`, and this
registry exists partly so that distance stays visible.

## 6. Maintenance

| ID | Rule |
| -- | ---- |
| `H-R05` | A new PACK-16D source is added **here**, with the next contiguous `H-*` ID and every field in §2's shape. It is never introduced in a prose document |
| `H-R06` | An `H-*` entry is never edited to point at a different source. A superseded source gets a new ID and the old entry records what superseded it. `H-01`…`H-05` were rewritten in place this round because each still names **the same source**, with a corrected role, a corrected version or a withdrawn digest; `H-03`'s script changed but its source — the OpenSSL Project's Ed25519 — did not |
| `H-R07` | An earlier round's source is cited in §3 as inherited, never re-minted as an `H-*`. The same source under two IDs is how a registry starts disagreeing with itself. The one admitted exception is `H-08`, bounded by `H-R09` |
| `H-R08` | If a later round obtains a primary-source vector for one of `H-06`'s six operations, `H-06` is **narrowed by a new entry**, and `PRIMARY_SOURCE_UNAVAILABLE` in code must lose that operation in the same change |
| `H-R11` | **A blocked entry is re-attempted, not quoted from memory, and that is what eventually cleared these two.** `H-01`'s access paths and `H-10`'s lock regeneration were re-run every round and failed every time, with verbatim transcripts kept in `PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md` rather than summarised. Because the failing commands were on record, running them on a network-enabled host produced evidence that sits beside the failures in the same document. A blocker asserted once and thereafter carried forward on a previous round's word is indistinguishable from an excuse — and, unlike this one, would never have become checkable |
| `H-R12` | **An entry's `provenance_status` and the acceptance matrix must agree.** `H-01` says `SATISFIED` and `AM-79` says `SATISFIED`, on the same commit pin and the same digest. The rule exists because these two once drifted apart — a registry admitting a gap while a matrix row claimed a pass — and an audit caught it. The drift is as possible in this direction as in the other, so the agreement is on the recorded evidence, not on the round's sense that the matter is now settled |
| `H-R10` | **A withdrawn digest is never restored by editing this file.** `H-01`'s `source_sha256` is filled in by running the commands in the artefact's `auditor_action` on a machine with network access and recording the commit SHA alongside it. A digest that appears here without a commit pin is a defect |

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
