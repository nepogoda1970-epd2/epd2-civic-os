# Changelog

## [0.16.0] - PACK-16D reference cryptographic implementation, atomic persistence, test vectors and verification harness (FINAL CORRECTED CANDIDATE)

### Network-enabled finalization — lockfile regeneration, immutable ElectionGuard provenance, final acceptance alignment

The two findings the previous pass recorded as environmental blockers have
been cleared on a host with the network access they needed. **No
cryptographic work was done**: no algorithm, guardian path, checkpoint
semantic, atomic transaction, sealed-batch rule or conformance oracle was
touched.

- **`DEPENDENCY LOCK: REGENERATED`.** `uv lock` and
  `rm -rf .venv && uv sync --all-groups --frozen` (`Checked 61 packages`) ran
  on the network-enabled host. `uv.lock` goes from `1a1e5a72…d543` to
  `b2d0775458…8066`: `cryptography 46.0.7` resolves from
  `https://pypi.org/simple` with `sha256:` hashes on all 43 artefacts, plus
  `cffi 2.1.0` and `pycparser 3.0`. 149 lines added, 0 removed, **0 existing
  package versions changed**. The lock was **verified, not accepted** —
  parsed as TOML, checked for a registry source, artefact hashes, membership
  of the `epd2-voting-service` dependency graph rather than the workspace
  root, and a resolved version satisfying every clause of the declared
  specifier.
- **`IMMUTABLE UPSTREAM IMPLEMENTATION PROVENANCE: RECORDED`.**
  `microsoft/electionguard-rust` at commit
  `520651138110a13f777409e96606454df928ceac` (2025-02-02),
  `src/eg/src/standard_parameters.rs`, raw-byte SHA-256
  `ad38bfa68d31131a7d721e08d359224b21e967aae4d517534a60a109e10f5770`,
  retrieved 2026-08-03. `unpinned_reason` and `auditor_action` were removed
  **in the same change** that added the pin, which a test enforces: a
  repository keeping an excuse beside the thing the excuse was for is telling
  a reader two incompatible stories. The digest an earlier round computed over
  a markdown rendering stays **withdrawn** and was not restored.
- **Pinning the implementation source did not promote it.** It stays
  `is_normative: false`; the normative reference remains the ElectionGuard
  Design Specification v2.1.0 at a versioned release asset, and the parameter
  values continue to rest on that specification and on the offline
  reconstruction in `derivation` — neither of which consults the Rust file.
- **Two things were verified elsewhere, and say so.** The frozen install and
  the upstream byte fetch happened on the network-enabled host. The build
  session verified the lock's parsed contents, asserted the imported
  `cryptography` version-identical to the locked resolution, checked the pin's
  internal consistency and re-derived every parameter offline — it did not
  re-run `uv sync` and did not re-fetch the bytes.
  `source_sha256_verification_scope` records that in the artefact, and one
  command settles it: `curl -sL <pinned-url> | sha256sum`.
- **`AM-79` and `AM-89` promoted to `SATISFIED` — on evidence, not on the
  blockers' removal.** Each of the ten conditions across the two rows is
  asserted by a named offline test. The previous pass's defect was a status
  drifting ahead of its evidence; promoting because an obstacle disappeared
  would be the same error pointed the other way. Matrix: 90 rows, **76
  `SATISFIED`, 6 `PARTIALLY SATISFIED`, 3 `DEFERRED`, 4 `BLOCKED`, 1 `NOT
APPLICABLE`**.
- **Every dual-state test branch is gone.** While the blockers were open, the
  dependency and provenance tests were deliberately written to pass in both
  states, because a permanently red test trains a reader to ignore red. That
  accommodation ended the moment the facts existed, or it would have become a
  check that cannot fail. A `null` `upstream_commit`, a missing lock entry, an
  abbreviated hash, a URL pinning a different commit than the field beside it,
  or an outstanding-lock notice outliving its cause each fail now.
- **`OD-P16D-16` and `OD-P16D-17` CLOSED** on recorded command output.
  **Nothing else moved:** `VO-08`, external cryptographic review, a fully
  independent verifier, full ElectionGuard ecosystem interoperability,
  constant-time production assurance, production HSM and key custody, the
  production guardian ceremony and legal certification all remain **OPEN**.
- **`PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md` converted to a RESOLVED
  historical record** rather than deleted. The failed transcripts are
  reproduced unchanged under an explicit `HISTORICAL FINDING` heading: a
  resolved blocker whose evidence has been tidied away is indistinguishable
  from one that was never real.
- **One transcription discrepancy recorded rather than silently corrected.**
  The finalization brief quoted the new lock digest as `02d0775458…`; the
  digest over the delivered file's bytes is `b2d0775458…`. They agree in 63 of
  64 hex characters, which no byte-level corruption produces. The computed
  value governs, because it is the one anybody can reproduce from the file.
- **0 files added, 0 deleted, 24 modified.** `package-lock.json` and
  `services/voting-service/pyproject.toml` unchanged; no migration, API
  implementation, event schema, frontend file, CI workflow or version constant
  touched; no file under `docs/canonical/` modified.
- **Verification.** 5851 Python tests passed, 5 skipped, 0 failed, no
  `--ignore`; 506 in the reference suite; `ruff check`, `ruff format --check`
  (498 files) and `mypy services/voting-service` (70 source files) clean; all
  four repository scripts pass.
- `REPOSITORY_VERSION` stays 0.16.0, `CANON_VERSION` stays 0.8.0, `ADR-102`
  stays `proposed`, `VO-08` stays **OPEN**, and PACK-17 is **not started**.

### Lockfile, provenance and acceptance-matrix correction pass (superseded by the finalization above)

A third independent audit passed **every cryptographic finding** — the
vetted provider, the removal of the hand-written Ed25519, checkpoint
authenticity, the real `EPD2-CRYPTO-1`, both guardian paths, the
target-profile cross-implementation core and archive hygiene. It raised
three items. One was fixable in this environment and is fixed; two were
not, and are recorded as blocked rather than worked around.

- **`AM-79` corrected from `SATISFIED` to `PARTIALLY SATISFIED`.** The row
  claimed the parameter set was _immutably provenanced_ while its own
  evidence column recorded that the commit, the pinned URL and the source
  digest were all absent. **Nothing new was learned to force the
  downgrade** — the facts were already in the artefact, the evidence
  registry and the previous handover. What was wrong was the status sitting
  on top of them. An evidence column that stays honest while a status
  column drifts optimistic is invisible to anyone who reads only the
  status, and it is exactly what an audit reading both will catch.
- **`DEPENDENCY LOCK: BLOCKED BY ENVIRONMENT`. `FROZEN CLEAN INSTALL: NOT
EXECUTED`.** `cryptography>=46.0.7,<47` stays declared and stays absent
  from `uv.lock`. `uv lock` and `uv sync --all-groups --frozen` were
  **re-run this round** and failed again on a proxy 403 — `Host not in
allowlist: pypi.org` — as did a clean-environment attempt. Hand-editing
  the lock is prohibited and was not done. `NOT EXECUTED` rather than
  "failed": a run ending in a proxy 403 produced no verdict about this
  repository.
- **`IMMUTABLE UPSTREAM IMPLEMENTATION PROVENANCE: PARTIALLY SATISFIED`.**
  The **normative** source stays pinned to a versioned release asset with
  its digest in the artefact. The **corroborating implementation** source
  could not be pinned: three access paths refused by **two distinct
  mechanisms** — `api.github.com` by a per-repository access broker,
  `raw.githubusercontent.com` and `git clone` by the egress allowlist. **No
  commit SHA and no byte-exact digest was invented.** An earlier round's
  digest, computed over a markdown rendering, stays withdrawn.
- **The source hierarchy is now declared, not inferred.** `source.hierarchy`
  names normative / corroborating / local artefact; `is_normative` is `true`
  on one block and `false` on the other; and `source.corroborating.role`
  states it is not a substitute for the specification. The failure mode this
  guards against is a reader treating a reference implementation's source
  file as normative.
- **New: `PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md`** — every command
  attempted and every error output, verbatim. A blocker with no
  reproduction is indistinguishable from an excuse; a reviewer with network
  access can run the same six commands and see a different result.
- **Tests now parse `uv.lock` as TOML rather than searching it as text**, and
  the dependency guard grew from 3 to 7 tests. Five provenance tests were
  added. **All twelve are written to pass in both the blocked and the
  resolved state on purpose**: a test that stays red until somebody gets
  round to it trains a reader to ignore red. What they forbid is the state
  that would actually mislead — a gap with nothing saying so.
- **No cryptographic, guardian, checkpoint, conformance, transaction or
  sealed-batch code was modified.** 1 file added, 0 deleted, 11 modified.
  `uv.lock` and `package-lock.json` unchanged.
- **Verification.** 5847 Python tests passed, 5 skipped, 0 failed, no
  `--ignore`; 504 in the reference suite; ruff, `ruff format --check` (498
  files) and `mypy services/voting-service` (70 source files) clean; all
  four repository scripts pass.
- `REPOSITORY_VERSION` stays 0.16.0, `CANON_VERSION` stays 0.8.0, `ADR-102`
  stays `proposed`, `VO-08` stays **OPEN**, and no file under
  `docs/canonical/` was modified.

### Final correction pass — vetted cryptographic provider, immutable parameter provenance, target-profile conformance

A second independent audit passed the parameter profile, the target-profile
crypto tests, both guardian paths, checkpoint signature _semantics_ and
archive hygiene. It failed one thing and half-passed two, and all three are
addressed here.

- **The signature primitive is no longer ours.** The previous round
  implemented Ed25519 from RFC 8032 in the standard library and defended it
  on the grounds that it was a published standard, implemented as written,
  and cross-checked against OpenSSL. Every fact in that defence was true and
  the conclusion was wrong: the round had optimised for **"add no
  dependency"** when the property that mattered was **"implement no
  cryptographic primitive"**. `crypto/ed25519.py` is **deleted** — not
  archived, not deprecated — and `crypto/signature_provider.py` is a thin
  port over `cryptography` 46.0.7 (OpenSSL 3.5.6): a Protocol with six
  operations, one active implementation, strict raw canonical encodings,
  fail-closed verification, and **no fallback** of any kind. An `ast` test
  fails if any module re-adds curve arithmetic under another name, and a
  subprocess test — with a control run, so it cannot pass for the wrong
  reason — proves the import raises when the library is absent.
- **The parameters no longer depend on a URL at all.** The artefact's
  authoritative reference moved from a mutable `/main/` branch to the
  **specification at its versioned release asset**, with its SHA-256
  recorded **in the artefact** rather than only in an evidence register.
  More importantly it gained a `derivation` block: `p` is reconstructed
  **offline** from the published `ln 2` rule (3305 bits, computed locally as
  `2·atanh(1/3)`) plus a recorded 279-bit offset, and `q`, `r` and `g`
  follow in closed form. A URL says where bytes came from; this says the
  bytes are the ones the published rule produces.
- **The previous round's source digest was withdrawn, not relabelled.** It
  had been computed over a markdown rendering rather than the raw file. The
  field is now `null` with `NOT RECORDED` and a stated reason: this
  environment's proxy blocks github.com, api.github.com and every CDN
  mirror, so no commit SHA and no byte-exact digest could be obtained
  (`OD-P16D-17`). Keeping a number that looks like a file digest and is not
  would have been worse than having none.
- **All twelve cross-implementation core operations now run on
  `EPD2-CRYPTO-1` itself**, not on the fast test group — parameter digest,
  both encodings, selection encryption, selection proof, ballot hash,
  confirmation code, accumulation, guardian commitment, decryption share,
  3-of-5 combination and tally recovery — from one deterministic fixture set
  with fixed nonces, plus two invalid fixtures that stay **inside the
  subgroup** so they are refused by the mathematics rather than a cheap
  structural check. The oracle is handed the ballot's _fields_ and rebuilds
  the canonical bytes itself, because handing it the producer's encoding
  would test the hash and not the encoding.
- **Five conformance classifications replace three.** One
  `cross-implementation` label covering both profiles is exactly how it
  stayed invisible that most checks ran on a group no election will use.
- **A pre-existing repository defect surfaced and was fixed.** A contract
  test had been _skipping_ rather than passing since PACK-16D first landed,
  because PyYAML was not importable — hiding ~65 reference-package reason
  codes that had never been checked against the voting service's contract
  registry, through two rounds and two audits. Verified pre-existing against
  the untouched source tree, then fixed by excluding the reference subtree
  by path with the reason recorded. **A skipped test is not a passing test.**
- **One thing is unfinished, and it is stated at the top of the handover
  rather than the bottom.** `cryptography` is declared in `pyproject.toml`
  and **absent from `uv.lock`**: regenerating the lock re-resolves the whole
  workspace against an index this environment blocks with HTTP 403, and
  hand-editing a lock is prohibited. **This round does not claim that a
  frozen install of this repository produces a working reference
  implementation.** `uv sync --all-groups --frozen` was run: it built every
  workspace member and then failed downloading a third-party wheel — a
  network failure, not a lock inconsistency. The gap is held open by a test
  and a `LOCK REGENERATION OUTSTANDING` notice that the same test forbids
  outliving its cause (`OD-P16D-16`).
- **Constant-time is narrowed, not closed.** Ed25519 signing moved to
  OpenSSL, which pursues side-channel resistance as a design goal — a real
  risk reduction and **not an assurance**, since EPD² measured nothing. The
  guardian secret operations and secret-nonce use remain pure Python.
  `OD-P16D-05` stays the production blocker. A compiled native artefact is
  now in the runtime path, which is stated rather than netted off.
- **Verification.** 5847 Python tests passed, 5 skipped, **no `--ignore`**
  (previously 5616 passed / 17 skipped _with_ one); 499 in the reference
  suite; `ruff check`, `ruff format --check` (497 files) and
  `mypy services/voting-service` (70 source files) clean; all four
  repository scripts pass. Line coverage 90.9 %. **`uv lock`, the entire npm
  side, hypothesis and branch coverage were still not executed** and none is
  claimed as a PASS.
- `REPOSITORY_VERSION` stays 0.16.0. **`CANON_VERSION` remains 0.8.0. No
  Canon domain, aggregate, event or invariant semantics changed. Canon
  compatibility metadata continues to support repository version 0.16.x** —
  no file under `docs/canonical/` was modified by this pass. `ADR-102`
  remains `proposed`; `VO-08` remains **OPEN**.

### Correction pass — cryptographic profile, threshold guardians, checkpoint authenticity and conformance

An independent audit of the first PACK-16D candidate returned **NOT
ACCEPTED**, passing the harness and failing four things: the actual
`EPD2-CRYPTO-1` profile, the threshold guardian model, checkpoint
authenticity and external conformance. All four are now implemented. The
version number does not move: a correction of a candidate that was never
accepted does not consume a new one.

- **`EPD2-CRYPTO-1` is real and loads.** The ElectionGuard 2.1 §3.1.1
  standard baseline parameters are committed as
  `crypto/profiles/EPD2-CRYPTO-1.json`, transcribed from
  `microsoft/electionguard-rust` `standard_parameters.rs` and **verified by
  mathematics rather than by trusting the fetch**: `q = 2^256 - 189`,
  `q | p-1`, `p = qr + 1`, `g^q = 1`, `p`/`q`/`r/2` probable-prime, both
  256-bit one-runs, and the `ln(2)` middle. A single wrong hex digit breaks
  all of them. `load_profile` has **no fallback** — no `except`, no default,
  no environment variable, no feature flag — proved by a test that parses
  its source. The two fast profiles are renamed
  `EPD2-TESTONLY-NOTCONFORMANT-*` so a name cannot invite the substitution
  the code forbids. `OD-P16D-01` is **closed**.
- **Threshold guardians.** Feldman verifiable secret sharing with Schnorr
  proofs of possession, Shamir decryption in the exponent, a generic
  `k`-of-`n` quorum engine, the PACK-16B 3-of-5 default and 4-of-7
  high-assurance configurations. No party ever holds the joint secret, the
  quorum comes from the ceremony transcript rather than the caller, `2k ≤ n`
  is refused, and compensated decryption exists only to raise. A 3-of-5
  ceremony and a complete election record both run on `EPD2-CRYPTO-1`.
  `OD-P16D-07` is **closed**.
- **Checkpoint authenticity.** Ed25519 (RFC 8032 PureEdDSA), implemented in
  the standard library because no lock change was possible, and **proved**
  to agree with OpenSSL out-of-process. The trust anchor is a
  `SignerRegistry` supplied alongside the export — no path reads a key out
  of the artefact being verified — with declared-in-advance rotation windows
  and five distinct failure outcomes. Authenticity and consistency are kept
  apart: two _validly signed_ conflicting checkpoints still return
  `BOARD_INCONSISTENCY`. `OD-P16D-09` is **closed** and is no longer a
  production blocker.
- **External conformance, in three named classes.** 2 primary-source and 11
  cross-implementation entries alongside the 23 internal-stability vectors,
  which keep their `interoperability NOT established` status. Two oracles
  share no code with the producer: OpenSSL out-of-process, and a Node.js
  verifier that re-derives the canonical encoding from the written grammar.
  Six operations have no published external vector and say so rather than
  being filled with a relabelled self-generated value.
- **A real defect the independent oracle found.** `encode_seq` concatenated
  its items raw after a count, so `SEQ([b"ab", b"c"])` and
  `SEQ([b"a", b"bc"])` produced identical bytes — two different sequences
  sharing a digest, in a function every protocol digest runs through.
  `encode_struct` had the same flaw. Both now length-prefix every member;
  every digest in the round changed, and the stability vectors caught it.
  **No self-generated vector could have found this**, which is the clearest
  evidence available that the audit was right.
- **Two new open decisions replace the three closed.** `OD-P16D-11`: the
  reference ceremony runs in one process with no authenticated channel, no
  HSM, no air gap and no custody. `OD-P16D-12`: the verifier checks a
  checkpoint against the signer registry it was given and cannot tell you
  that registry was authorised by the Election Board.
- **Constant-time was widened, not softened.** Four surfaces are now
  distinguished: public verification carries no secret, while guardian
  secret operations, secret-nonce use and Ed25519 private-key signing are
  all secret-bearing and none is constant-time. `OD-P16D-05` is now the
  round's **only** production blocker.
- **Verification after the correction.** 5616 Python tests passed (17
  skipped), 464 of them in the reference suite; `ruff check`,
  `ruff format --check` (496 files) and `mypy services/voting-service` (69
  source files) clean; all four repository scripts pass. Line coverage of
  the reference package is 90.9% (3816/4200) with the stdlib `trace`
  module. **`uv sync --frozen`, the entire npm side, hypothesis and branch
  coverage were still not executed** and none is claimed as a PASS.
- **No dependency and no lock file changed.** `uv.lock` and
  `package-lock.json` are unchanged and neither was hand-edited.
  `cryptography` and Node.js are used only by out-of-process test oracles.
- `REPOSITORY_VERSION` stays 0.16.0. **`CANON_VERSION` remains 0.8.0. No
  Canon domain, aggregate, event or invariant semantics changed. Canon
  compatibility metadata was updated to include repository version 0.16.x**
  — that widening happened in the 0.16.0 round, is correct, and is not
  reverted; this correction modified no file under `docs/canonical/`.
- `ADR-102` remains `proposed`, as do `ADR-099`, `ADR-100` and `ADR-101`.
  `VO-08` remains **OPEN**: having the published parameters is not having an
  assessment that they are appropriate for a binding German election.

### Original candidate pass

_The entries below describe the candidate the audit rejected. They are kept
as the record of what was delivered and when. **Where they conflict with the
correction section above, the correction section is current** — in
particular the profile availability, the guardian model, checkpoint
signature verification, the vector counts and the two production blockers
have all changed._

- **The first PACK-16 round that ships code.** PACK-16A specified the
  protocol, PACK-16B the parameters and ceremony, PACK-16C the casting,
  publication and record model. PACK-16D implements a _reference_ form of
  all three inside `services/voting-service`, under
  `epd2_voting_service.reference`: cryptography, canonical encoding,
  domain separation, randomness, ballot preparation, proofs, the two
  atomic transactions, sealed batches, the bulletin board, the election
  record and an independent verifier. **This is a reference
  implementation and a candidate for audit. It is not production code,
  not certified, and not legally activated.**
- **Zero new dependencies.** Finite-field exponential ElGamal, the NIZK
  proof family and the transparency log are built on `hashlib`, `hmac`,
  `secrets` and Python's arbitrary-precision integers. `uv.lock` and
  `package-lock.json` are byte-identical to 0.15.0. No cryptographic
  library was added, so none had to be assessed for abandonment,
  provenance or supply-chain risk this round.
- **`EPD2-CRYPTO-1` is registered but deliberately unavailable.** The
  published ElectionGuard 2.1 4096-bit `p` and `g` could not be obtained
  first-hand in this environment, and transcribing 1024 hex digits from a
  summarised source would be a fabrication. `load_profile("EPD2-CRYPTO-1")`
  therefore raises `ParameterProfileUnavailableError` rather than
  substituting anything, and two clearly banner-marked TEST profiles
  (4096/256 and 1024/160, both self-verified) carry the tests.
  `OD-P16D-01` owns closing this. `q = 2^256 - 189` _was_ confirmed
  first-hand and is asserted by test.
- **Eighteen defects were found by this round's own harness and readers,
  and every one was fixed in the implementation rather than documented
  around.** The two that mattered most: the idempotency check ran outside
  the transaction boundary, so two concurrent requests sharing a key could
  both observe "no record yet"; and the shared reserve was inferred from
  whatever capacity was left in a batch rather than read from the declared
  plan, which silently reintroduced adaptive overflow whenever a batch
  grew. The full list is in
  `docs/packs/PACK-16/PACK-16D-IMPLEMENTATION-REPORT.md` §7 — including a
  record digest that omitted the batch openings, decryption-share proofs
  bound to nothing, two verifiers that skipped a subgroup check, and a
  concurrency test whose own assertion was wrong about one run in thirty.
- **The Merkle construction was replaced, not patched.** The first draft
  duplicated the last node on odd levels, which makes two different leaf
  sequences share a root. `crypto/merkle.py` now follows the RFC 6962
  shape with EPD² domain separation, and adds consistency proofs, so
  rollback and equivocation **within one exported view** are detectable
  rather than merely named. Split view **across mirrors** is still not
  detected, because that mechanism remains unstandardised; `OD-P16D-06`
  owns it.
- **Verification.** 5513 Python tests passed (17 skipped), mypy clean
  across every group, `ruff check` and `ruff format --check` clean.
  361 of those tests are new PACK-16D tests: 23 test vectors across 20
  families, 36 negative-corpus cases, 15 properties, 9 concurrency races,
  11 fault points and 10 end-to-end scenarios. **`uv sync --frozen` and the whole
  npm side were not executed at all** - both registries return HTTP 403
  in this environment, exactly as `LOCAL_VERIFICATION.md` records. Line
  coverage of the reference package is 91.8% measured with the stdlib
  `trace` module; **branch coverage was not measured**, because neither
  `pytest-cov` nor `coverage` is installable here.
- **`VO-08` remains OPEN** and is carried into the implementation
  acceptance gates. No BSI conformity is claimed. Constant-time and
  side-channel behaviour is explicitly NOT claimed: Python's big integers
  are not constant-time, and `crypto/proofs.py` says so where a reader
  will see it. Two open decisions are **production blockers**:
  `OD-P16D-05` (no constant-time guarantee) and `OD-P16D-09` (checkpoint
  signatures are carried but never verified).
- `REPOSITORY_VERSION` 0.15.0 -> 0.16.0. **`CANON_VERSION` remains
  0.8.0**; PACK-16D's canon assessment concludes NO CANON CHANGE
  REQUIRED. `canon-version.json` changed only its non-canonical
  bookkeeping: `repository_compatibility` widened to `<0.17.0`.
- `ADR-102` is `proposed`. It does not declare `ADR-099`, `ADR-100` or
  `ADR-101` accepted; all four remain proposed pending review.

## [0.15.0] - voting trust boundary, eligibility & credential separation (FINAL PASS)

- **PACK-15 implementation candidate.** The separation between knowing who
  someone is and knowing that a vote was cast, implemented rather than
  specified. The design turns on ADR-093's structural cut: the spent-nonce
  record is a **set** with three columns and no value column, so no store,
  log, event, trace, backup or export contains both an assertion reference
  and a credential reference for the same participation.
- **Seven databases, not one.** The eligibility store, the Assertion
  Issuer store, the voting-credential store, the voting context registry
  and the three audit-stream stores are separate SQLite database files, so
  a foreign key across a trust boundary is not expressible rather than
  merely unwritten. Ten migration files across seven migration sets, with
  a shared dependency-free migration runner in `epd2-core`.
- **Exactly-once, split across the boundary.** The identity side enforces
  one assertion per participation unit (`participation_unit_ledger`
  primary key); the voting side enforces one credential per assertion
  nonce (`spent_nonce` primary key). Both are decided by the INSERT, so a
  concurrent second attempt loses on a constraint rather than on a
  check-then-act read that raced.
- **A versioned, transport-agnostic API**: 22 endpoints across four
  services over a shared contract layer in `epd2-core`, where a
  consequential endpoint may waive no obligation, an operation name may
  not exist on both sides of the boundary, and every response body is
  scanned at every nesting depth before it leaves.
- **Ten roles and eight structural separation rules**, validated at import
  time: no role holds eligibility, issuance and tally; the Credential
  Issuer holds no identity access; no auditor spans the identity-side and
  voting-side audit streams; privileged export and break-glass need two
  distinct approvers holding different roles.
- **89 reason codes.** `ALREADY_VOTED` and `PARTICIPATION_CONFIRMED` are
  deliberately absent and may never be added: to emit either, a component
  would have to know that a particular participant's credential was
  redeemed, which is exactly the linkage this pack removes.
- **Verification.** 5335 Python tests passed (5 skipped), mypy clean
  across every group, `ruff check` and `ruff format --check` clean, and
  all four repository scripts pass. **The npm side was not executed at
  all** - the registry returns HTTP 403, `node_modules` cannot be
  installed, and the five PACK-15 frontend files have never been run,
  type-checked or rendered. See `docs/handover/PACK-15-TEST-EVIDENCE.md`.
- **PACK-15 FINAL PASS — external GitHub Actions passed every stage:**
  983/983 repository paths, no forbidden paths, version consistency, Ruff
  format over 436 files, Prettier, Ruff lint, ESLint and mypy all PASS,
  5343 Python tests passed with 4 skipped, 3 `epd2-types` tests, 41 Node
  tests, 23 frontend tests, a successful Next.js production build with
  48/48 static pages, and 135 browser, visual and accessibility tests.
  See `docs/handover/PACK-15-FINAL-PASS-REPORT.md`.
- A stale nested copy of the repository at `epd2-civic-os/` (version
  `0.6.0`) was removed before this run and the tree re-verified from
  scratch; the Ruff count moved from 609 to 436, and **every verification
  artifact for a tree containing that directory is superseded.**
- **NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** The pipeline verifies
  the repository; it binds no provider and deploys nothing. Key custody is
  unbound and refuses, there is no transport layer, and SQLite remains the
  reference persistence. No CI check was weakened, no lock file was
  modified, and no test result was fabricated.

## [0.14.0] - identity, authentication & account security (FINAL PASS)

- **PACK-14 FINAL PASS — external GitHub Actions passed every stage:**
  867/867 repository paths, no forbidden paths, version consistency, Ruff
  format over 566 files, Prettier, Ruff lint, ESLint, mypy across all 23
  groups and both TypeScript typechecks all PASS, 4905 Python tests passed
  with 4 skipped, 3 `epd2-types` tests, 34 Node tests, 16 frontend unit and
  render tests, a successful Next.js production build with 46/46 static
  pages, and 108 browser, accessibility and visual tests. See
  `docs/handover/PACK-14-FINAL-PASS-REPORT.md`,
  `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md` and the raw
  transcript at `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION.log`.
- **NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** The pipeline verifies
  the repository; it binds no provider and deploys nothing. All four of
  PACK-14's security ports are still unbound and still **refuse**, the
  persistence path is still a SQLite reference path with no production
  database behind it, and the service boundary is still transport-agnostic
  with no HTTP surface or gateway in front of it.
- The round reached PASS as a candidate first. The candidate's own report
  and the local-verification caveats it recorded are retained in
  `docs/handover/PACK-14-IMPLEMENTATION-CANDIDATE-REPORT.md`, which is
  deliberately not rewritten to read as though it had always been a PASS;
  a superseding status note was added to it and to the ten
  implementation-round documents under `docs/packs/PACK-14/`, and nothing
  else in any of them changed.
- Extended `services/identity-service` in place with the six bounded
  contexts specification §4.1 assigns to it - Account Registry,
  Credential Registry, Authentication, Session Security, Recovery
  coordination and Identity-Proofing references - as internally separated
  modules with separate storage boundaries. **No parallel authentication
  service was created**, and ownership of canon 7.2's `Account` and canon
  7.3's `IdentityRecord` is unchanged.
- `FIR-INV-001` survives the round that most threatened it: **no global
  user ID exists**. Five identifier spaces are distinct Python types,
  what crosses a domain boundary is a purpose-scoped
  `ScopedIdentityReference` derived per purpose and per organizational
  scope, and every event payload passes `reject_prohibited_payload_keys`
  before an envelope exists.
- The account lifecycle is represented **without extending canon 7.2's
  six statuses** (OD-P14-01): `AccountLock`, a security-class
  `AccountRestriction`, `AccountClosureRequest` state and lifecycle
  outcomes, each separately queryable and separately reversible.
- Passkey-first authentication behind a `WebAuthnVerifier` port whose
  default binding **refuses**; controlled password fallback behind a
  `PasswordHasher` port whose default binding **refuses**. **No WebAuthn
  cryptography and no password-hashing algorithm is implemented in this
  repository.** A synced passkey caps at `substantial`; `high` requires a
  device-bound credential (OD-P14-08).
- `MfaFactorClass` has **no `sms_otp` member**: SMS OTP is not a login
  method, not a step-up factor and carries no assurance level at all
  (OD-P14-09). The system operates with no SMS provider.
- Session security with two mandatory deadlines and no sentinel for
  either, refresh-token families whose reuse revokes the family, and
  `SessionRecord` held as a **service-level aggregate** on PACK-12's
  `PrivilegedSession` precedent rather than added to canon (OD-P14-05).
- Step-up bound to an action **and an object version**: a confirmation
  obtained against version _n_ does not authorise version _n+1_
  (ADR-082).
- A per-workspace authentication bootstrap that is **explicitly not
  SSO** - single-use, audience-bound, no parent-domain cookie, no
  reusable cross-origin token (OD-P14-06) - and the WS-03
  `VotingHandoffArtifact`, whose issuance record carries no account
  reference of any kind so no pair of records resolves a redemption back
  to the holder (ADR-088). **No Voting Client is implemented.**
- The governed recovery workflow with revocation before completion, dual
  control, cooling-off, out-of-band notification, and the
  resulting-confidence rule that requires an explicit reason-coded risk
  acceptance for a shortfall (OD-P14-10).
- Added `contracts/reason-codes/pack-14.yml` (213 entries: 131 additive,
  22 redeclared from PACK-02/07/08/09, 60 `*_RECORDED` audit
  classifications derived mechanically from the event catalog).
  **There is no generic `AUTH_ERROR` and none may be added.**
- Fifty-nine event types in nine families, all on PACK-13's canonical
  envelope **unchanged**. `PUBLIC_PROJECTION_ALLOWED` is empty by design.
- `REPOSITORY_VERSION` 0.13.0 -> 0.14.0. **`CANON_VERSION` remains
  0.8.0**: the round amends no canon, reuses canon 19d.2's and 19d.8's
  existing four-value assurance scale rather than inventing an
  AAL-0…AAL-3 vocabulary, and adds no canonical enum value.
- `OD-P14-07` (retention durations) **remains open pending legal
  confirmation** and does not block the reference implementation: safe
  provisional schedules exist, deletion under a legal hold refuses, an
  unknown hold state fails closed, and a destructive disposition against
  an unconfirmed schedule is refused with
  `RETENTION_SCHEDULE_UNCONFIRMED`.
- **Correction round, 2026-07-30, before external CI.** The first
  candidate archive was reviewed and three findings were returned and
  fixed. No functional scope was expanded, no frontend was built, no
  dependency was added, no CI gate was weakened, no existing test was
  removed, and `REPOSITORY_VERSION 0.14.0` / `CANON_VERSION 0.8.0` are
  unchanged. The status remains `PACK-14 IMPLEMENTATION CANDIDATE
COMPLETE`. `docs/packs/PACK-14/PACK-14-IMPLEMENTATION-REPORT.md` §12
  records the three findings in full.
  1. **The persistence was metadata, not persistence.** Added ten real
     SQL migration artefacts under `services/identity-service/migrations/`
     and `migration_runner`, which applies them in order inside a single
     transaction with a recorded SHA-256 checksum and a compatibility
     check that refuses a database whose history disagrees with the files
     on disk; `sql_storage` with eleven durable adapters, a `UnitOfWork`
     transaction boundary and a monotonic optimistic-concurrency guard;
     `codecs`, a type-hint-driven serializer that keeps typed identifiers
     and timezone-aware timestamps intact and refuses raw `bytes` and
     naive datetimes; and `runtime`, the composition root. Applying the
     artefacts produces 29 tables and 35 indexes, 9 of them unique
     constraints (2 partial) and 10 of them expiry indexes.
     **This is a reference persistence path on SQLite through the
     standard library** — it adds no dependency, `uv.lock` and
     `package-lock.json` are unchanged, and **no production database is
     deployed and no production durability is claimed.** The `InMemory*`
     adapters remain as explicit **test** adapters and are no longer any
     runtime's default binding.
  2. **The breached-password default was permissive.** Removed
     `NoBreachedPasswordChecker`. The unbound default is now
     `UnboundBreachedPasswordChecker`, which raises
     `BREACH_CHECK_UNAVAILABLE` rather than returning either boolean:
     **no checker means no password enrollment and no password
     replacement.** `DeterministicBreachedPasswordChecker` is a declared
     test double. `PasswordDegradedModeDecision` is the one governed
     exception and permits **authentication against an already stored
     hash only** — it has no field that could re-open enrollment, and a
     test asserts the field set.
  3. **`api.py` was an endpoint catalogue, not a boundary.** Added
     `service_api`, a transport-agnostic runnable adapter: request
     parsing and validation, envelope validation in a fixed order (origin
     → session → idempotency → version), audience assertion, durable
     idempotency, a registered reason code on **every** response
     including successes, and `assert_response_safe` in
     `ApiResponse.__post_init__` so a response carrying a prohibited
     identifier or a secret cannot be constructed. `ROUTED_OPERATIONS`
     (12) and `CONTRACT_ONLY_OPERATIONS` (30) are named constants, so no
     document can imply that all 42 catalogued operations run. **No HTTP
     server, no production gateway, no public deployment and no real
     external provider.**
  - 46 tests added in `services/identity-service`
    (`test_pack14_persistence.py`, `test_pack14_service_api.py`, and the
    fail-closed breach-boundary section of `test_pack14_security.py`) and
    14 at the repository level
    (`tests/repository/test_pack14_default_binding.py` plus the migration
    -vocabulary parity section of
    `tests/repository/test_pack14_duplicated_logic_parity.py`). Local
    suite: **4898 passed, 5 skipped**.
- **Not implemented, and not claimed:** production IAM, real eID, real
  email or SMS delivery, production HSM or KMS, a production database or
  any operational durability, an HTTP surface or production gateway, a
  complete Voting Client, membership or candidate eligibility, voting
  credential issuance, ballots, tallies, a full legal electronic
  signature, or the full Account & Security FRONT-PACK (`FIR-UX-011`
  stays future).
- **PACK-13 (`0.13.0`, FINAL PASS) is now the previous PASS baseline.** The
  PACK-14 FINAL PASS archive supersedes it as the authoritative cumulative
  baseline; nothing in PACK-01—PACK-13 was rewritten to achieve that.
- **FINAL PASS packaging round, 2026-07-30.** Documentation and status
  only: the register, this changelog, `README.md`, `docs/adr/README.md`,
  `services/README.md`, `services/identity-service/README.md`, the
  acceptance matrix's and FIR coverage matrix's status blocks, one
  superseding status note on the PACK-14 specification and on each of the
  eleven implementation-round documents, and the three new handover
  documents. Three files were adopted from the externally verified tree
  because the packaging sandbox's copies were stale: the PACK-09, PACK-11
  and PACK-13 external-CI transcripts, whose content is identical and
  three of whose lines carried a stray `CR`. No service module, test,
  reason code, migration artefact, ADR, contract, frontend file, route,
  visual snapshot or CI definition changed, and neither version moved.

## [0.13.0] - production data plane & contract evolution (FINAL PASS)

- **PACK-13 FINAL PASS — external GitHub Actions passed every stage:**
  800/800 repository paths, no forbidden paths, version consistency, Ruff
  format over 520 files, Prettier, Ruff lint, ESLint, mypy across all 23
  groups and both TypeScript typechecks all PASS, 4625 Python tests passed
  with 4 skipped, 34 Node tests, 16 frontend unit and render tests, a
  successful Next.js production build, and 108 browser, accessibility and
  visual tests. See `docs/handover/PACK-13-FINAL-PASS-REPORT.md`,
  `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION-RESULT.md` and the raw
  transcript at `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log`.
- **NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** The pipeline verifies
  the repository; it deploys nothing. Every storage adapter in
  `services/data-plane-service` is in memory.
- The round reached PASS as a candidate first. The candidate's own report
  and the local-verification caveats it recorded are retained unchanged in
  `docs/handover/PACK-13-IMPLEMENTATION-CANDIDATE-REPORT.md`, which is
  deliberately not rewritten to read as though it had always been a PASS.
- Added `services/data-plane-service` (22 source modules, 20 test
  modules, 555 tests): the reference implementation of PACK-13's
  transactional persistence contracts, the canonical schema registry and
  its format-specific canonicalization, the deterministic compatibility
  checker with its semantic-risk escalation, API and event contract
  evolution, the migration framework and its five automated gates, the
  backfill runner, the transactional outbox, at-least-once delivery with
  effectively-once consumer effect, projection governance, the search and
  export persistence contracts, retention and legal-hold bindings, the
  PACK-12 privileged gates, the structural boundary guards, the
  thirty-seven canonical events, the storage ports and their in-memory
  adapters, the governed commands, and the contract-level administrative
  surfaces.
- Added `contracts/reason-codes/pack-13.yml` (125 entries: 78 additive
  PACK-13 codes, 10 redeclared unchanged from earlier packs, and 37
  `*_RECORDED` audit classifications, one per event). There is no generic
  `DATA_ERROR` and no generic `CONFLICT`, per `P13-RSN-002`.
- Added the accepted ADR-069 through ADR-078 and the eleven PACK-13
  specification documents under `docs/packs/PACK-13/`. The ADRs move from
  `proposed` to `accepted` and record that the decision is implemented in
  **reference form**.
- Extended `docs/packs/PACK-13/PACK-13-ACCEPTANCE-MATRIX.md` with an
  implementation-status appendix covering all 176 criteria (implemented
  component, test file, evidence, status, deferred dependency). **Recorded
  as met: 0** — unchanged by the PASS, because the criteria whose evidence
  is a database grant inventory, a live catalog snapshot, a role inventory
  or an egress-control review describe an environment no pipeline creates.
- Extended `docs/packs/PACK-13/PACK-13-FIR-COVERAGE-MATRIX.md` with an
  implementation-coverage appendix. The matrix still contains **zero**
  `implemented` values, now asserted structurally by
  `tests/repository/test_pack13_fir_matrix.py` (`AC-P13-155`).
- Updated `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`:
  round records 1.8 (candidate), 1.9–1.12 (the register addenda) and 1.13
  (FINAL PASS); `FIR-BASE-001` now names the PACK-13 FINAL PASS archive
  as the authoritative cumulative baseline with PACK-12 as the previous
  one; `FIR-ROADMAP-003` moves `approved` → `scheduled` → **`implemented in
reference form`**, and not to `implemented` outright; and section 21
  records PACK-01 through PACK-13 as PASS. No entry deleted, no identifier
  reused, no status downgraded, no second register created.
- Added register section 26, **Canonical Forms, Submissions & Official
  Renditions** (`FIR-FORM-001` … `FIR-FORM-005`, all `approved`): the
  cross-cutting future layer for governed form definitions, per-domain form
  inventories, governed German content, submissions and multi-channel
  official renditions, together with the reporting rule that every later
  domain PACK must carry a `Forms and Official Documents Coverage` section.
- Added register section 27, **Cross-cutting procedural, trust and
  operational foundations** (`FIR-RULE-001`, `FIR-REF-001`,
  `FIR-DELIVERY-001`, `FIR-TRUST-001`, `FIR-REPRESENT-001`,
  `FIR-INCLUSION-001`, `FIR-QUALITY-001`, `FIR-CONFIG-001`,
  `FIR-IMPORT-001`, `FIR-SERVICE-001`, all `approved`): the governed rules
  registry, reference-data and taxonomy registry, official delivery and
  service evidence, electronic signature/seal/trusted-timestamp framework,
  representation and assisted action, alternative-channel procedure, data
  quality and reconciliation, governed operational configuration, legacy
  import, and the service catalogue.
- Added register section 28, **Frontend design, visualization and
  interaction governance** (`FIR-UX-003` … `FIR-UX-010`, all `approved`):
  the design-system and component governance, information architecture and
  navigation, interaction patterns for consequential actions, system states
  and recovery, content and terminology, responsive behaviour, visual status
  semantics, and design evidence for frontend acceptance. It establishes the
  approved FRONT-00/FRONT-01 implementation — the existing public pages,
  shared components, actual design tokens, typography, spacing rhythm,
  colours, borders, radii, page widths, grid and navigation character, and
  the accepted reference screenshots — as the **authoritative visual
  baseline**. A future FRONT-PACK must inventory what exists, extract the
  real tokens, classify each pattern as reuse/extend/replace, justify every
  replacement, compare against the accepted screenshots and preserve
  recognisable continuity. The baseline is a reference, not a pixel freeze:
  justified improvement is allowed, unrelated redesign is not.
- All three sections are recorded as **future implementation debt**:
  nothing in them is implemented, none changes any canon, none extends
  PACK-13's scope, and **none is covered by the external CI run**, which
  verified the implementation candidate before they were written.
- The register in this archive is the consolidated version supplied for
  this round, adopted verbatim at its canonical path, with only the four
  status changes this round is required to make: the FINAL PASS round
  record, the `FIR-BASE-001` baseline pointer, `FIR-ROADMAP-003`'s status,
  and section 21's implementation summary. All 140 FIR entries are present
  and no identifier is duplicated.
- Added `docs/handover/PACK-13-IMPLEMENTATION-CANDIDATE-REPORT.md`,
  `docs/handover/PACK-13-KNOWN-LIMITATIONS.md`,
  `docs/handover/PACK-13-FINAL-PASS-REPORT.md`,
  `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION-RESULT.md` and
  `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log`.
  `docs/handover/PACK-13-SPEC-ADR-REPORT.md` is retained unchanged as the
  specification round's own report and is deliberately not rewritten as an
  implementation report.
- Renamed nothing in earlier packs. One naming decision was forced:
  the data-plane suite's application test is
  `test_data_plane_application.py`, not `test_application.py`, because
  `services/document-service/tests/test_privacy_boundary.py` imports a
  helper with `from test_application import Flow` and a second module of
  that name collected earlier in directory order would shadow the one it
  means.
- Repository version `0.12.0` -> `0.13.0`. Canon version unchanged at
  `0.8.0`: this round amends no canon, and the PACK-13 canon assessment
  records why none is needed.
- **What this round does not do.** No production PostgreSQL, cloud
  database, real broker, external schema-registry product, production
  search engine, production IAM or multi-region topology is deployed or
  claimed. Every storage adapter is in memory. No identity domain
  (PACK-14), eligibility, credential, voting or tally domain
  (PACK-15/16), and no backup or restore capability (PACK-17). No
  arbitrary-SQL console and no universal administration surface. The
  voting domain's broker topics, broker deployment arrangement,
  connection-pool topology, service names, credential topology and
  transport provider are deliberately **not decided** — they are
  PACK-15/16's, taken with that pack's own threat model.
- **PACK-12 (`0.12.0`, FINAL PASS) is now the previous PASS baseline.**
  The PACK-13 FINAL PASS archive supersedes it as the authoritative
  cumulative baseline; nothing in PACK-12 was rewritten to achieve that.
- **Documentation correction, 2026-07-30, after the first candidate
  archive.** One approved requirement was found missing from
  `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` and is now
  recorded there as `FIR-PROG-003` — Public Presentation of Adopted
  Programme and Projects (status `approved`, section 17): the adopted
  programme is the primary content of the public `Programm` page, with its
  adoption facts and version history directly available; projects appear
  only as a single compact `Projekte in Beratung` card per thematic
  section, explicitly marked `Noch nicht beschlossen` and linking to a
  separate page; and the adopted/not-adopted distinction never rests on
  colour alone. It is a **future frontend obligation**, not a PACK-13
  implementation item. The correction touched only the register, the
  candidate report and this changelog: no code, test, CI configuration,
  ADR, PACK-13 architecture decision, repository version or canon version
  changed. It remains `approved` after the PASS.
- **FINAL PASS packaging round, 2026-07-30.** Documentation and status only:
  the register, this changelog, `README.md`, `docs/adr/README.md`,
  `services/README.md`, `services/data-plane-service/README.md`, the PACK-13
  known-limitations document, the acceptance matrix's and FIR coverage
  matrix's status blocks, one superseding status note on the PACK-13
  specification, and the three new handover documents. Two files were
  adopted from the externally verified tree because the packaging sandbox's
  copies were stale: `uv.lock`, which now registers
  `epd2-data-plane-service` as a workspace member, and
  `docs/frontend/FRONT-00-PAGE-INVENTORY.csv`, whose content is identical
  and whose line endings are not. No service module, test, reason code,
  ADR, contract, frontend file, route or visual snapshot changed, and
  neither version moved.

## [0.12.0] - privileged administration, authorization-aware search & governed export (FINAL PASS)

- Added `services/privileged-access-service` (17 source modules, 16 test
  modules, 327 tests): the privileged-access grant lifecycle, the governed break-glass
  workflow, tamper-evident privileged sessions, authorization-aware search,
  governed data export, DLP assessment and transforms, and statistical
  disclosure control - three logical bounded contexts sharing one package
  boundary, one command frame and one audit path.
- Added `contracts/reason-codes/pack-12.yml` (141 entries: 98 refusals, 43
  audit classifications; 13 reused verbatim from earlier packs).
- Added proposed ADR-061 through ADR-068 and the nine PACK-12 specification
  documents under `docs/packs/PACK-12/`.
- Merged sections 24 and 25 into
  `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`, adding
  thirteen entries (`FIR-UX-*`, `FIR-ID-*`, `FIR-COMM-004`, `FIR-SEARCH-*`,
  `FIR-SUPPORT-*`, `FIR-METRIC-*`). The existing repository file was the
  merge base; no entry was deleted, no status downgraded, and no second
  register was created.
- Repository version `0.11.0` -> `0.12.0`. Canon version unchanged at
  `0.8.0`: this round amends no canon.
- **PACK-12 FINAL PASS — external GitHub Actions passed every stage:**
  728/728 repository paths, no forbidden paths, Ruff format, Prettier, Ruff
  lint, mypy and TypeScript typecheck all PASS, 4062 Python tests passed
  with 4 skipped, 108 browser tests passed, accessibility and visual checks
  PASS. See `docs/handover/PACK-12-FINAL-PASS-REPORT.md` and
  `docs/handover/PACK-12-EXTERNAL-CI-VERIFICATION-RESULT.md`.
- Reached through two CI corrections, both retained in the history: a
  documentation correction (removing an inaccurate "locally verified" claim
  and fixing the module inventory) and Prettier formatting, which included
  deleting the stray duplicate `docs/handover/PACK-12-FIR-COVERAGE-MATRIX.md`.
  The canonical matrix is `docs/packs/PACK-12/PACK-12-FIR-COVERAGE-MATRIX.md`.
- **NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** PACK-12 provides no
  production database, production search engine, external IAM, real DLP
  provider, real notification delivery, production session assurance, voting
  capability or legal activation. `AC-P12-090` remains deferred.

## FRONT-00 foundation candidate correction 0.1.1

- Replaced five simplified examples with faithful non-production migrations of
  the exact `EPD_Front.zip` source compositions.
- Added the missing component/native-pattern catalogue, 13 rendered behavior
  tests, Playwright visual/browser coverage, axe and keyboard accessibility
  coverage, and CI commands.
- Corrected source/migration/showcase terminology and the collision-safe mypy
  command without changing repository 0.9.0 or canon 0.7.0.

## FRONT-00 Implementation Candidate - 2026-07-27

- Extracted EPD_Front visual tokens into the existing Next.js web shell.
- Added shared shell/components, 19 presentation states, five representative
  fixtures and declarative route/workspace/storage/telemetry policies.
- Added architecture/component tests and FRONT-00 documentation.
- Added Proposed ADR-044 through ADR-047.
- No dependency, backend, canon-version or repository-version change.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.11.0] - governed documents & evidence (implementation)

CLAUDE-PACK-11 implementation round. The first executable slice of the
governed-document and evidence bounded context canon 19f.22 assigns to
PACK-11, shipped as `services/document-service`. **This is `PACK-11
GOVERNED DOCUMENTS & EVIDENCE 0.11.0 — FINAL PASS`, verified by an
external GitHub Actions run (see
`docs/handover/PACK-11-GOVERNED-DOCUMENTS-EVIDENCE-0.11.0-FINAL-PASS-REPORT.md`).
A green pipeline is not a claim of legal validity, evidential
admissibility, signature verification, tamper resistance or production
readiness — each of those needs its own gate and none has been passed.**
`CANON_VERSION` stays at `0.8.0`: this round amends no canon, it
implements a context canon already assigned.

Implements `FIR-ROADMAP-001` (PACK-11 Governed Documents & Evidence) and
`FIR-INV-010` (document version integrity) in full. Provides foundation
only - explicitly not full implementation - for `FIR-DEC-001`,
`FIR-DEC-002`, `FIR-CAND-001`, `FIR-COMM-001`, `FIR-PROG-002`,
`FIR-INIT-021`, `FIR-PAY-003` and `FIR-DATA-003`. See
`docs/packs/PACK-11-FIR-TRACEABILITY.md`.

### Added

- `services/document-service` - thirteen modules, the sole authoritative
  owner of the governed-document and evidence context: `exceptions` (one
  class per registered reason code), `domain` (value objects, identity
  minimisation, the content boundary, the governed taxonomies),
  `versions` (immutable versions and the SHA-256 hash-linked chain that
  implements `FIR-INV-010`), `authorization` (eight roles, twenty-one
  governed actions, the symmetric incompatibility matrix, per-act
  separation of duties, access profiles and independence),
  `documents` (the `GovernedDocument` aggregate, review requirements,
  approval, publication authorization, renditions, supersession,
  revocation), `evidence` (evidence records, chains of custody, sealed
  bundles), `determinations` (the governed signature and admissibility
  determinations and reference resolution - ADR-053's four PACK-11
  consumer requirements), `references` (the typed references this context
  exports and consumes), `events` (twenty-five canonical event builders),
  `storage` (ports and in-memory adapters, including a content-addressed
  `ContentStore`; no delete method exists on any port), `projections`
  (restricted and public read models, neither authoritative, neither
  carrying content) and `application` (the command and query layer).
- `contracts/reason-codes/pack-11.yml` - seventy-one entries: thirty-three
  `DOCUMENT_*` refusals, twenty `AuditEvent.reason_code` classifications
  for successfully-audited acts, and eighteen codes reused verbatim from
  PACK-02, PACK-04 and PACK-07 through PACK-09. There are deliberately no
  `source: canon-0.8.0` entries: canon section 24 registers no document or
  evidence code at all, so every `DOCUMENT_*` code is additive and
  justified in ADR-055.
- `contracts/schemas/` - four PACK-11 JSON Schemas (governed document,
  document version, evidence bundle, publication rendition).
- `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` - the
  master future-implementation register, placed at its canonical
  repository path and updated with exact PACK-11 status, evidence paths
  and remaining work per entry.
- Proposed ADR-055 through ADR-060.
- `docs/packs/PACK-11-*` (specification, implementation, FIR
  traceability, acceptance matrix, cross-pack boundaries, threat model,
  open decisions), `docs/architecture/document-service.md`,
  `docs/architecture/document-version-integrity.md`,
  `docs/contracts/document-command-query-contracts.md` and
  `docs/handover/PACK-11-*`.
- Repository-level boundary tests: `document-service` imports only
  `epd2_core` and `epd2_audit_core`, no service imports it back, its
  storage exposes no delete-shaped method, and its manifest declares no
  other service package.

### Changed

- `REPOSITORY_VERSION` `0.10.0` -> `0.11.0` (Python and TypeScript). A new
  bounded context is a minor bump per canon section 25.
- `docs/canonical/canon-version.json`: added
  `document_context_implementation_status = "reference_implementation"`,
  and widened `repository_compatibility` from `<0.11.0` to `<0.12.0`.
- `scripts/check_canon_0_8_0.py`: `EXPECTED_REPOSITORY_VERSION`
  `0.10.0` -> `0.11.0`, plus a new eighteenth check that the
  document/evidence context is declared and has a runtime behind it.
  `CANON_AMENDED_AT_REPOSITORY_VERSION` is deliberately left at `0.9.0`.

### Not changed

- `docs/canonical/TZ-00-domain-event-canon.md` is untouched. `CANON_VERSION`
  stays `0.8.0`.
- PACK-09's and PACK-10's placeholder reference types (`DocumentRef`,
  `EvidenceRef`, `MinutesRef`, `DocumentReference`, `EvidenceReference`)
  are left exactly as they are and are **not** rewritten to import
  PACK-11's real ones. The boundary those placeholders exist to hold is
  the boundary this round keeps.
- No production database, event bus, external anchor for the version-chain
  head, HTTP surface or frontend. No signature verification and no legal
  or admissibility judgement: this service records determinations made by
  an authority and reports their absence as absence.

## [0.10.0] - party finance, accounting & Rechenschaftsbericht (implementation)

CLAUDE-PACK-10 implementation round. The first executable slice of the
party-finance bounded context canon 0.8.0 section 19f defines, shipped as
`services/finance-service`. **This is a `PACK-10 PARTY FINANCE 0.10.0
CANDIDATE`, not a PASS release, and not a claim of production, legal,
banking or external-authority readiness (`ФИН-43`).** `CANON_VERSION`
stays at `0.8.0`: this round amends no canon, it implements one.

### Added

- `services/finance-service` — twelve modules, the sole authoritative
  owner of the section-19f context: `exceptions` (one class per
  registered reason code), `domain` (`Money` in integer minor units with
  an explicit currency and scale and no floating point anywhere,
  `FinancePartyHandle`, `OrganizationalScopeRef`, the
  identity-minimisation rejection list), `authorization` (the six finance
  roles, the action-authority table, the canon 19f.14 incompatibility
  matrix, separation-of-duties assertions), `ledger` (chart of accounts,
  accounting periods with explicit timezones, balanced double-entry
  postings, correction by reversal or correcting entry), `records`
  (contributions and their governed exceptional states, sponsorship,
  external financial benefit, expense claims, payment authorisation and
  settlement, assets, obligations, inter-unit transfers), `reporting`
  (reporting obligation, perimeter, frozen snapshot, the twelve-state
  `Rechenschaftsbericht` lifecycle, the independent audit engagement),
  `events` (all seventy-two canonical section-20.17 event builders plus
  full-state payloads for Audit Core hashing), `references` (typed,
  content-free references to PACK-09, PACK-11 and PACK-35 records),
  `storage` (a `Protocol` port and an in-memory reference adapter per
  aggregate, an idempotency store and an event sink — and no delete
  method anywhere), `projections` (derived, versioned,
  never-authoritative read models with statistical disclosure control),
  and `application` (forty-two commands and five queries, each routed
  through one guard frame: scope, authority, role compatibility, conflict
  declaration, idempotency, optimistic concurrency, then domain
  transition, audit append and event publication).
- `services/finance-service/tests` — the committed test suite for the
  above.
- `contracts/reason-codes/pack-10.yml` — 96 entries: the forty-five
  `FINANCE_*` codes canon section 24 introduced with the 0.8.0
  amendment, nineteen additive PACK-10 codes (four refusals canon has no
  code for, fifteen `AuditEvent.reason_code` classifications for
  successfully-audited acts), and thirty-two pre-existing codes reused
  verbatim rather than shadowed by `FINANCE_`-prefixed duplicates.
- `docs/packs/PACK-10-IMPLEMENTATION.md`, `docs/architecture/
finance-service.md`, `finance-ledger-model.md`,
  `finance-reporting-lifecycle.md`, `finance-separation-of-duties.md`,
  `finance-publication-projection.md`, `docs/contracts/
finance-command-query-contracts.md` and
  `docs/handover/PACK-10-IMPLEMENTATION-REPORT.md`.

### Changed

- `REPOSITORY_VERSION` `0.9.0 → 0.10.0` in
  `packages/python/epd2-core/src/epd2_core/version.py` and
  `packages/typescript/epd2-types/src/version.ts`. A new bounded context
  is a minor bump under canon section 25.
- `docs/canonical/canon-version.json`:
  `finance_context_implementation_status` `not_implemented →
reference_implementation`, and `repository_compatibility` widened from
  `>=0.1.0 <0.10.0` to `>=0.1.0 <0.11.0` so canon 0.8.0 still admits the
  repository that implements it. `minimum_repository_version` and
  `amended_at_repository_version` stay at `0.9.0`: the amendment does not
  postdate itself.
- `scripts/check_canon_0_8_0.py`: check 5 inverted. It asserted that
  `services/finance-service` did **not** exist, which was correct for the
  canon round and false the moment the implementation round shipped; it
  now asserts that the runtime exists, carries its twelve modules, offers
  no deletion method, and that no finance-named path appears under
  `packages/` or `frontend/`. Checks 2, 3 and 4 follow the new version and
  status.
- `docs/architecture/data-ownership.md`: the twenty-one finance rows move
  from "Not implemented" to `finance-service`.
- `pyproject.toml`, `uv.lock`, `Makefile`, `scripts/check_repository.py`
  and `tests/contract/_schema_helpers.py`: the new workspace member, its
  required paths, its typecheck line and its reason-code registry.

### Not in this round

- No production persistence, no event bus, no bank or payment-provider
  integration, no external-authority submission channel: every storage
  adapter is in-memory and PACK-13 owns the production data plane.
- No operational finance frontend. FRONT-00 and FRONT-01 are untouched,
  including all 45 committed visual snapshots and both lockfiles.
- No canon amendment. `CANON_VERSION` stays `0.8.0` and
  `docs/canonical/TZ-00-domain-event-canon.md` is byte-identical to the
  0.8.0 text.
- No `Budget` or `ReconciliationRecord` aggregate: canon 19f.1 names
  both, and this round ships their events and projections but not their
  aggregates. See `docs/packs/PACK-10-IMPLEMENTATION.md` for the full
  deferral list.

## [Unreleased] - canon minor version 0.8.0 (Party Finance & Financial Accountability Context)

CLAUDE-PACK-10 canon-amendment round. **Canon-only: no runtime
implementation, no service, no contract, no migration, no frontend page
and no business test was added, and `REPOSITORY_VERSION` is unchanged at
`0.9.0`.** The result is a **PACK-10 CANON 0.8.0 CANDIDATE** for review,
not a PASS release: ADR-054 and ADR-048 through ADR-053 all remain
`proposed`.

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.7.0 →
0.8.0` (ADR-054, `proposed`) — the seventh edit to this document's own
  text since its original acceptance (after ADR-010's `0.1.0 → 0.2.0`,
  ADR-013's `0.2.0 → 0.3.0`, ADR-018/ADR-020's `0.3.0 → 0.4.0`,
  ADR-023/ADR-025's `0.4.0 → 0.5.0`, ADR-026 through ADR-031's `0.5.0 →
0.6.0`, and ADR-037's `0.6.0 → 0.7.0`). Adds a new section 19f
  ("Партийные финансы и финансовая отчётность / Party Finance &
  Financial Accountability Context"), inserted between sections 19e and
  20 — the same non-renumbering technique used for 19a–19e. The section
  defines twenty-one authoritative finance entities (`FinanceAccount`,
  `AccountingPeriod`, `JournalEntry`, `FinancialTransaction`,
  `ImportBatch`, `ReconciliationRecord`, `FinanceContribution`,
  `SponsorshipAgreement`, `ExternalFinancialBenefit`, `ExpenseClaim`,
  `PaymentAuthorization`, `Budget`, `FinancialAsset`,
  `FinancialObligation`, `ReportingObligation`,
  `ReportingPerimeterDefinition`, `FinanceReport`, `ReportSnapshot`,
  `AuditEngagement`, `FinancePolicy`, `FinancePartyHandle`), all owned by
  `Finance Service`; the terminology separations that keep
  `FinanceContribution` apart from canon 13.2's `Contribution`,
  `FinanceAccount` from canon 7.2's `Account` and the accounting ledger
  from canon 19a.1's public ledger; deterministic money semantics
  (integer minor units, explicit currency, no floating point); the
  immutable balanced double-entry ledger and correction by reversal or
  correcting entry; accounting-period closure and dual-control reopening;
  the transaction register, provenance, import batches and duplicate/
  replay detection; the contribution lifecycle with its governed
  exceptional states, the anti-splitting aggregation rule and
  related-party/intermediary aggregation; sponsorship and financially
  measurable external benefit with the PACK-35 boundary; expense and
  reimbursement with authorization separated from execution; assets,
  obligations and the rule that budgets never overwrite ledger facts; a
  forty-five-rule finance-invariant register (`ФИН-01` – `ФИН-45`); four
  new institutional `role_code` values (`finance_administrator`,
  `payment_authorizer`, `payment_executor`, `report_signatory`)
  extending 19e.15's open list, the extended 19e.16 incompatibility
  baseline including the adopted owner decision that
  `finance_administrator` is incompatible with
  `organizational_administrator` in the same legally relevant scope, and
  four action-level authorities that deliberately do not become
  institutional roles; the purpose-scoped `FinancePartyHandle` with its
  authorized, audited resolution boundary and the explicit statement
  that pseudonymization is not anonymity; reporting obligation,
  perimeter and immutable report snapshot; the twelve-state
  `Rechenschaftsbericht` lifecycle (`draft`, `internally_reviewed`,
  `auditor_reviewed`, `approved`, `signed`, `submitted`,
  `externally_acknowledged`, `externally_accepted`, `published`,
  `amended`, `restated`, `superseded`) in which submission is neither
  acknowledgement nor acceptance and telemetry never creates legal
  effect; independent finance audit with a create-once `AuditConclusion`;
  organizationally scoped consolidation that grants no lower-scope write
  authority; governed effective-dated finance policies with historical
  version binding and no statutory threshold as a canon constant; safe,
  derived, non-authoritative public financial projections under
  statistical disclosure control; the cross-pack boundaries toward
  PACK-09, PACK-11, PACK-12, PACK-13, PACK-14 and PACK-35; and an
  implementation gate (19f.25). Section 20.17 adds seventy-two finance
  events with owner, aggregate, event version, required safe metadata,
  prohibited payload, cross-pack consumers and public-projection rules;
  section 22 gains twenty-one ownership rows; section 23 gains
  twenty-five forbidden-link entries; section 24 gains forty-five
  `FINANCE_*` reason codes — no existing entity, status, event, owner or
  reason code was renamed, redefined or repurposed, and no naming
  conflict was found.
- `docs/canonical/canon-version.json`: `canon_version` `0.7.0 → 0.8.0`,
  plus explicit compatibility metadata — `minimum_repository_version`
  `0.9.0`, `amended_at_repository_version` `0.9.0`, and
  `finance_context_implementation_status` `not_implemented`.
  `repository_compatibility` deliberately stays `>=0.1.0 <0.10.0`: a
  repository at `0.9.0` consumes canon `0.8.0`, and widening the range
  would pre-authorize an implementation round that has not happened
  (OD-20).
- `packages/python/epd2-core/src/epd2_core/version.py` and
  `packages/typescript/epd2-types/src/version.ts`: `CANON_VERSION`
  `0.7.0 → 0.8.0`; `REPOSITORY_VERSION` unchanged at `0.9.0`.
- `packages/python/epd2-core/tests/test_version.py` and
  `packages/typescript/epd2-types/tests/version.test.ts`: expected canon
  version updated to `0.8.0` with the round's narrative comment. No test
  was weakened or removed.
- `docs/canonical/README.md`, `docs/adr/README.md`, `README.md`,
  `docs/architecture/data-ownership.md`,
  `docs/architecture/service-boundaries.md`: canon `0.8.0`, the ADR-054
  index row and narrative, the twenty-one finance ownership rows (all
  marked not implemented) and the finance trust boundaries.

### Added

- `docs/adr/ADR-054-canon-0.8.0-party-finance-context-additions.md` —
  `proposed`. The canon-amendment ADR.
- `scripts/check_canon_0_8_0.py` — sixteen standalone canon-level checks
  (canon version, repository version, compatibility metadata, absence of
  any finance runtime implementation, bounded-context registration, the
  twenty-one ownership rows, `FinancePartyHandle` not being a global
  identity, the finance-to-voting prohibitions, ledger immutability and
  balancing, the auditor incompatibility, submission versus acceptance,
  PACK-11 and PACK-35 ownership, event owners and payload restrictions,
  reason-code uniqueness, and ADR status integrity).
- `tests/repository/test_canon_0_8_0_amendment.py` — the pytest wrapper
  over those checks, in the established `tests/repository` style.
- `docs/handover/PACK-10-CANON-0.8.0-REPORT.md` — the round's report.
- `docs/packs/PACK-10-CANON-0.8.0-ACCEPTANCE-MATRIX.md` — acceptance
  evidence and the `ФИН` ↔ `HI` coverage map.
- `docs/packs/PACK-10-CANON-0.8.0-COMPATIBILITY.md` — compatibility
  statement and the reason-code registry diff (45 new, 32 reused,
  rejected collisions), the event-canon diff (72 vs the specification's 69) and the report-state naming diff.

### Unchanged, deliberately

- `REPOSITORY_VERSION` stays `0.9.0`; the latest released CHANGELOG
  heading stays `## [0.9.0]`.
- No `services/finance-service`; no file anywhere under `services/`,
  `packages/`, `frontend/` or `contracts/` whose name contains
  `finance`; no migration, OpenAPI operation, runtime JSON Schema,
  frontend page or business test.
- `contracts/reason-codes/pack-10.yml` was **not** created: canon
  section 24 is the registry of record for a canon round, and a pack
  registry file whose codes no service uses would either fail
  `tests/contract/test_reason_codes_registry.py` or require weakening it
  (`PACK-10-CANON-0.8.0-COMPATIBILITY.md` section 3.4).
- PACK-01 through PACK-09 implementation, existing backend behaviour,
  accepted ADR content and existing domain ownership: untouched.

## [Unreleased] - PACK-10 specification candidate (documentation only)

CLAUDE-PACK-10 (Party Finance, Rechenschaftsbericht & Financial External
Influence) specification and ADR phase. **Documentation only: no
production code, no new service, no runtime contract, no version
change.** The result is a **PACK-10 SPECIFICATION CANDIDATE** for
architectural review, not a PASS release.

### Added

- `docs/packs/PACK-10-SPECIFICATION.md` — the normative PACK-10
  specification: eleven capability groups (ledger and accounting
  periods, income, expenditure, donations and contributions, sponsorship
  and financial external influence, expense and reimbursement, assets
  and obligations, budgets, `Rechenschaftsbericht` lifecycle, finance
  audit, public transparency); fifty-five numbered hard invariants with
  planned enforcement point, mechanism, test, reason code and cross-pack
  dependency; the classification of all thirty-nine candidate concepts
  into twenty-one authoritative aggregates, entities, create-once
  records, value objects and derived read models; the
  identity-minimization model (purpose-scoped `FinancePartyHandle`, no
  global user ID, restricted resolution surface, audited access); the
  PACK-08 organizational and consolidation model; PACK-09 and PACK-11
  integration boundaries; governed effective-dated finance policies; a
  proposed event taxonomy; and a proposed reason-code catalogue.
- `docs/adr/ADR-048-pack-10-finance-service-decomposition.md` —
  `proposed`. One bounded context `services/finance-service` with
  explicitly separated internal modules.
- `docs/adr/ADR-049-authoritative-finance-ledger-and-correction-model.md`
  — `proposed`. Layered model: the double-entry general ledger is
  authoritative for monetary effect, the transaction register for the
  business fact and its provenance; integer minor units only; posted
  entries immutable; corrections by governed reversal; period lock and
  controlled reopening.
- `docs/adr/ADR-050-purpose-scoped-financial-party-references-and-aggregation.md`
  — `proposed`. Purpose-scoped opaque party handles with a governed
  matching act, lawful aggregation without a platform-wide identifier,
  and an explicit statement that pseudonymization is not anonymity.
- `docs/adr/ADR-051-rechenschaftsbericht-lifecycle-snapshot-and-authority-semantics.md`
  — `proposed`. Ten-state report lifecycle, create-once source
  snapshot, submission ≠ acceptance (only a PACK-09
  `NoticeEffectDecision` reaches `accepted_by_authority`), publication ≠
  approval, append-only version chain, frozen historical perimeter.
- `docs/adr/ADR-052-finance-authority-separation-and-independent-audit.md`
  — `proposed`. Four new institutional roles and five action-level
  separations, the extended non-combinable-role matrix that fills
  PACK-08 section 9.3's explicit reservation, and independent finance
  audit with a create-once `AuditConclusion`.
- `docs/adr/ADR-053-pack-10-pack-09-pack-11-pack-35-boundaries.md` —
  `proposed`. Ownership matrix across PACK-08/09/10/11/12/13/14/35, the
  decidable financial-value versus influence-relationship test, and the
  determination that PACK-09's `FinanceEvidenceRef` remains sufficient
  with a documentation-level semantic correction and additive PACK-10
  reference exports.
- `docs/packs/PACK-10-OPEN-DECISIONS.md` — twenty-two unresolved
  owner/legal/security questions (OD-1 through OD-22), each with a
  recommended default where one is defensible, explicitly marked where
  that default is legally unverified.
- `docs/packs/PACK-10-IMPLEMENTATION-PLAN.md` — gates, eight-phase plan,
  file inventory, carried-over conventions, sequencing risks.
- `docs/packs/PACK-10-ACCEPTANCE-MATRIX.md` — the planned domain,
  application, storage, contract, architecture and repository tests,
  with a coverage map from every hard invariant to at least one named
  test.
- `docs/packs/PACK-10-THREAT-MODEL.md` — thirty-five threats with
  protected asset, attacker or failure mode, trust boundary, mitigation,
  detection, audit evidence, residual risk and future-pack dependency.
- `docs/packs/PACK-10-CROSS-PACK-BOUNDARIES.md` — ownership matrix,
  reads, consumed and exported references, PACK-11 requirements, PACK-35
  integration points, forbidden edges.
- `docs/packs/PACK-10-CANON-AMENDMENT-ASSESSMENT.md` — the explicit
  determination that a canon amendment is **required** (option 2), concept
  by concept.
- `docs/packs/PACK-10-CANON-AMENDMENT-PROPOSAL.md` — the proposed canon
  minor-version addition (`0.7.0 → 0.8.0`): new section 19f, new section
  20.17 event catalogue, new section 22 ownership rows, new section 23
  forbidden links, new section 24 reason codes, with compatibility and
  migration impact. **Not applied.**
- `docs/handover/PACK-10-SPEC-REPORT.md` — the round's handover report.

### Changed

- `docs/adr/README.md` — six new index rows (ADR-048 through ADR-053,
  all `proposed`) and a narrative entry for this round.
- `README.md` — a PACK-10 status entry identifying the pack as
  specification-only and not implemented.

### Unchanged, deliberately

- `REPOSITORY_VERSION` stays `0.9.0`; `CANON_VERSION` stays `0.7.0`;
  package versions unchanged.
- `docs/canonical/TZ-00-domain-event-canon.md`,
  `docs/canonical/canon-version.json`, `contracts/**`, `services/**`,
  `packages/**`, `frontend/**`, `tests/**`, CI configuration and
  `scripts/check_repository.py`'s required-path list — none touched. New
  documentation paths were deliberately not added to the checker's
  required-path list, the same precedent ADR-026 through ADR-037 already
  set (recorded in that file's own comment).

## [Unreleased] - canon minor version 0.7.0 (Organization & Regional Scope Context)

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.6.0 →
0.7.0` (ADR-037, accepted, following ADR-032 through ADR-036's own
  prior acceptance in the PACK-08 spec-correction round) — the sixth
  edit to this document's own text since its original acceptance
  (after ADR-010's `0.1.0 → 0.2.0`, ADR-013's `0.2.0 → 0.3.0`,
  ADR-018/ADR-020's `0.3.0 → 0.4.0`, ADR-023/ADR-025's `0.4.0 → 0.5.0`,
  and ADR-026 through ADR-031's `0.5.0 → 0.6.0`). Adds a new section 19e
  ("Организация и региональная авторизация — расширение / Organization
  & Regional Scope Context"), inserted between sections 19d and 20, the
  same non-renumbering technique used for 19a/19b/19c/19d. Extends
  `Organization` (8.1) with six additive fields
  (`organization_profile`, `parent_reference`, `effective_from`,
  `effective_until`, `dissolved_at`, `successor_reference`); confirms
  `CivicSpace` (8.2) unchanged; defines four wholly new canonical
  entities owned by `organization-service` (`OrganizationalUnit`,
  `OrganizationalRelation`, `OrganizationalHierarchyOverlapPolicy`,
  `OrganizationalInheritancePolicy`) plus `OrganizationalAuthority`
  (distinct from, and cross-referenced only by opaque reference with,
  the unchanged `RoleAssignment`, 8.4) and the reusable
  `OrganizationalScope` value shape (not separately owned, the same
  status as `RedactionManifest`/`AIDisclosurePackage`). Canonizes:
  four non-interchangeable concepts (Organization/Jurisdiction/
  CivicSpace/process-local Scope) and a no-silent-field-reinterpretation
  rule for `organization_id`/`jurisdiction`/`region_code`/`scope_id`/
  `civic_space_id`; multiple typed directed graphs for organizational
  relationships (not a strict tree), with relation-type-specific cycle
  and overlap rules; `parent_reference`'s non-authoritative,
  derived-projection status; uniform effective dating (valid_from/
  valid_until/recorded_at/supersedes/historical queryability/
  future-dated changes/overlap validation) across `Organization`/
  `OrganizationalUnit`/`OrganizationalRelation`/`OrganizationalAuthority`;
  canonical reorganization rules (creation/activation/suspension/
  dissolution/merger/split/successor/renaming/territorial reassignment)
  with a hard no-automatic-rights-transfer invariant; default-deny
  regional scope authorization with six explicit access modes and hard
  anti-confused-deputy/anti-role-name-as-proof/no-universal-
  administrator rules; inheritance-policy ownership (restrict-never-
  broaden); a 90-day default maximum for temporary supervision; seven
  named institutional roles and a minimum eight-bullet non-combinable-
  role baseline (subject to legal refinement); role/authority lifecycle
  rules; extended identity-minimization rules; and a six-category
  classification requirement for `RoleAssignment.scope_id` (8.4 itself
  unchanged in fields/status/owner). Section 20.5 (Organization events)
  gains thirteen entries and full payload/timing/audit/privacy
  documentation; section 22 gains five new ownership-matrix rows;
  section 23 gains new forbidden-link entries; section 24 gains ten new
  reason codes (`ORGANIZATION_NOT_ACTIVE` through
  `HISTORICAL_SCOPE_NOT_EFFECTIVE`) — no existing code or event name
  renamed or repurposed; no naming conflict found.
  `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py`, and
  `packages/typescript/epd2-types/src/version.ts` updated to match, with
  both version-consistency unit tests updated and
  `scripts/verify_versions.py` passing; `REPOSITORY_VERSION` is
  unchanged (`0.7.0`) — this is a canon-only change, per CLAUDE-PACK-08's
  own canon-amendment round (`docs/adr/ADR-037`;
  `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`). No
  `organization-service` code, database, migration, event bus, frontend,
  schema, OpenAPI file, or reason-code registry file was created.
- `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`.

### Verified

- **Local, honest self-report only — no external GitHub Actions run was
  performed or is claimed for PACK-08, at any stage, including this
  canon-amendment round.** Fresh local re-run in this sandbox: Ruff
  (lint + format) clean; mypy clean for `epd2-core`/`scripts`/
  `tests/repository`/`tests/contract` and for all 15 services
  individually; Python test suite: 2020 passed, 5 skipped, 1 failed (the
  expected, self-resolving `test_no_forbidden_paths_present`
  cache-artifact detection — 0 real failures); all 402 required paths
  present; version consistency passed. Full detail:
  `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md` section 6.

## [0.9.0] - compliance, records governance & legal workflows (implementation)

CLAUDE-PACK-09. One wholly new service (`compliance-service`, ADR-038)
plus its contracts and tests. No canon change: `CANON_VERSION` stays
`0.7.0`, and no canon-owned file was touched.

### Added

- `services/compliance-service` — PACK-09's one new service, owning six
  entity families across `domain.py`, `application.py`, `events.py`,
  `storage.py` and `exceptions.py`:
  - **Records governance** (ADR-039): `RetentionPolicy` (append-only by
    `(policy_id, policy_version)`), `RetentionStartEvent` (retention never
    starts implicitly), `GovernedRecord`, `DisposalEligibility`,
    `DestructionAuthorization`, `DestructionEvidence` (create-once).
    Destruction is a three-step controlled workflow — evaluate → authorize
    → execute — and no store in the service exposes a delete method.
  - **Legal Hold** (ADR-039): `LegalHold` with three states
    (`active`/`released`/**`indeterminate`**), additive scope over record
    ids / record classes / case ids, append-only history, and explicit
    release. An indeterminate hold fails closed with
    `LEGAL_HOLD_STATE_UNKNOWN`.
  - **Data Catalog & Processing Registry** (ADR-040): `DataAsset`,
    `ProcessingActivity`, and `LegalBasis` as a closed, managed
    classification enum. Mandatory retention references are resolved
    against the policy store, not merely typed. Identity field names are
    rejected at construction.
  - **Governed cases & deadlines** (ADR-041): `ProceduralCase` with
    constrained transitions, required steps and referenced evidence;
    `DeadlineDefinition` with a required IANA timezone; and
    `ProceduralDeadline` whose `status` and `due_at` are _derived_ from an
    append-only history — neither is a stored field.
  - **Data-subject and legal requests** (ADR-040/ADR-041):
    `DataSubjectRequest` holding an identity-verification _status_ plus an
    opaque reference, and no identity attribute anywhere.
  - **Party arbitration and disputes** (ADR-042): `DisputeParties`,
    `CaseRoleAssignment`, `ConflictOfInterestDeclaration` (explicit
    `ConflictState`, not free text), `CaseDecision`, `AppealReference`, and
    `domain.assert_decision_maker_eligible` — the single gate that blocks
    self-appointment, party appointment, handler appointment, undeclared
    conflicts and blocking conflicts.
  - **Organizational scope isolation**: `RequestContext` plus
    `CrossScopeAuthorityGrant` with enumerated `ScopeCapability` values.
    No hierarchy-derived inheritance; crossing a boundary requires a grant
    issued by the target organization _and_ presented by the caller.
- ADR-038 through ADR-042 (full template, accepted 2026-07-26).
- `contracts/reason-codes/pack-09.yml` — 40 codes, each carrying all seven
  fields `epd2_core.reason_codes.ReasonCodeRegistry` requires.
- Fifteen new entity schemas and eight new event payload schemas under
  `contracts/schemas/` and `contracts/events/`.
- `contracts/openapi/pack-09.yaml` — 28 operations, every one tagged
  `compliance-service`, with request bodies, reason-coded error responses
  and no DELETE method anywhere.
- Repository verification wiring for PACK-09: `PACK09_*` constants in
  `tests/contract/_schema_helpers.py`; a pack-09 row in
  `tests/contract/test_reason_codes_registry.py`; PACK-09 sections in
  `tests/contract/test_openapi_contract.py`,
  `test_ct00_08_identity_leakage.py` and
  `test_ct00_09_vote_linkability.py`; a new
  `tests/contract/test_ct00_01_pack09_schema_validation.py`; PACK-09
  boundary tests in `tests/repository/test_service_boundaries.py`; and 44
  new required paths in `scripts/check_repository.py`.

### Changed

- `REPOSITORY_VERSION`: `0.8.0 → 0.9.0`. `CANON_VERSION` remains `0.7.0`;
  `docs/canonical/canon-version.json` `repository_compatibility` widened to
  `>=0.1.0 <0.10.0`.
- `Makefile` `typecheck` target now also runs `mypy` over
  `services/organization-service` and `services/compliance-service`, which
  were both absent from it.

### Added — Architecture & Domain Framework 0.8.1 (same 0.9.0 round)

The **EPD² Architecture & Domain Framework 0.8.1** (Roadmap Amendment)
became the authoritative scope document for PACK-09 mid-round. Nothing
above was rewritten; the following was added to the same service, under
the same dependency rule, with `CANON_VERSION` still `0.7.0`.

- `services/compliance-service/src/epd2_compliance_service/casework.py` —
  the **common legal-case substrate** (Framework 13.1): `LegalCase`
  (status derived from an append-only transition history, never stored),
  `JurisdictionDetermination` (appended, never rewritten; a transfer
  keeps the outgoing determination's own authority reference and gains a
  pointer to its successor), `CaseParty` and `RepresentationMandate`
  (enumerated authorities, not a role name), `Filing` (immutable docket:
  store-assigned sequence, rejection preserved in place, correction by
  supersession, `submitted_at` and `received_at` distinct), `Hearing`,
  `InterimMeasure` (a _granted_ measure is constructible only by a human
  authority, and only with an end or review date plus reasons),
  `ProceduralDecision` (effect, finality and enforceability as three
  independent derived facts), `Remedy`, `RecusalRecord` and
  `ReplacementAssignment`, plus the gates
  `assert_may_decide_substantively`, `assert_due_process_complete` and
  `assert_actor_not_recused`.
- `services/compliance-service/src/epd2_compliance_service/notices.py` —
  the **official-notice trust boundary** (ADR-043, new): `OfficialNotice`
  (an authorized object; starts nothing), `ServiceAttempt` (provider
  telemetry, with `is_reconciled` gating every deemed-service rule),
  `NoticeEffectDecision` (the only object that can start a procedural
  deadline) and `DeadlineTrigger` (create-once per deadline).
  `TriggerSource` names `delivery_telemetry` and `read_telemetry`
  precisely so both can be refused _by name_ rather than by omission.
- `services/compliance-service/src/epd2_compliance_service/dataprotection.py`
  — **data-protection governance and the DPIA gate**:
  `DPIARequirementDetermination` (recorded even when the answer is "no",
  because its absence is what blocks activation),
  `DataProtectionImpactAssessment`, `ProcessingActivationDecision`,
  `TransferAssessment`, `ConsentWithdrawalRecord`, plus
  `assert_activation_permitted` and `assert_dpo_independence`.
- `services/compliance-service/src/epd2_compliance_service/references.py`
  — the **stable typed references** PACK-09 publishes to
  PACK-10/11/19/21-24 (`LegalCaseRef`, `DeadlineRef`, `NoticeEffectRef`,
  `HoldRef`, `RecordClassRef` and siblings), plus explicit
  `PlaceholderRef` forward declarations for objects later packs own.
  There is no `PersonRef`, `UserRef` or `MemberRef` and there must never
  be one.
- `domain.py` additions: `RecordClass` (record owner and disposition
  authority must differ), `DataClassification`,
  `SearchExportEligibility`, `HoldPropagationRecord`, `PropagationState`
  and `assert_hold_propagation_resolved`.
- `events.py`: **33 new event types** (41 in total), each with a wire
  payload that carries no party or authority handle at all;
  `ALL_EVENT_TYPES` and `NON_LEGAL_EFFECT_NOTICE_EVENT_TYPES` make the
  set and the prohibition testable.
- `application.py`: 34 new commands, each with scope guards, `event_id`
  idempotency through Audit Core, an audit append with canonical
  before/after hashes, and reason-coded refusal — plus
  `assert_destruction_propagation_resolved` as a separate assertion
  rather than a widened `authorize_destruction` signature.
- `storage.py`: 18 new Protocol/in-memory store pairs, including
  create-once stores for notice effects and deadline triggers and an
  append-only filing store that compares ten immutable fields on update.
- `contracts/`: 22 new entity schemas, 33 new event payload schemas,
  34 new OpenAPI operations (62 in total), and 32 new refusal reason
  codes plus 18 additive audit classifications in `pack-09.yml` (88 in
  total).
- `docs/adr/ADR-043-official-notice-legal-effect-trust-boundary.md` —
  the round's one new ADR. ADR-038 through ADR-042 each gained a
  Framework 0.8.1 amendment section.
- `docs/handover/PACK-09-KNOWN-LIMITATIONS.md` — what this pack does not
  do, and where each partial guarantee ends.
- Tests: `test_casework.py`, `test_notices.py`, `test_dataprotection.py`
  and `test_framework_application.py` in the service suite;
  `tests/contract/_pack09_framework_samples.py` and
  `test_ct00_01_pack09_framework_schema_validation.py`; new PACK-09
  sections in `test_openapi_contract.py` and
  `test_ct00_08_identity_leakage.py`.

### Changed — Architecture & Domain Framework 0.8.1 (same 0.9.0 round)

- Two reason codes introduced earlier in this same **unreleased** 0.9.0
  round were renamed in place rather than duplicated:
  `CROSS_ORGANIZATION_CASE_ACCESS_DENIED` → `CROSS_SCOPE_ACCESS_DENIED`
  and `DECISION_AUTHORITY_MISSING` → `DECISION_AUTHORITY_DENIED`. The old
  exception class names remain as aliases, so no call site changed.
  Registering synonyms would have left two codes meaning one thing.
- `notices.determine_notice_effect` returns a recorded `NOT_EFFECTIVE`
  determination when every authorized attempt positively failed, rather
  than raising. A refusal that raised would leave no record for the
  parties to see or challenge.
- Two constructor guards that previously raised a bare `ValueError` now
  raise their registered reason-coded errors:
  `InterimMeasure` without an end or review date
  (`INTERIM_MEASURE_AUTHORITY_DENIED`) and `DeadlineTrigger` from a
  telemetry source (`DEADLINE_TRIGGER_INVALID`).
- `scripts/check_repository.py`: 489 → 554 required paths.

### Verified

- **PACK-09 IMPLEMENTATION 0.9.0 — EXTERNAL CI PASS.** The full pipeline
  ran on GitHub Actions (ubuntu-latest, Python 3.12, Node.js 22) against
  the locked toolchain and passed: 556 required paths, no forbidden
  paths, Prettier PASS, `ruff format` PASS, `ruff check` PASS, `mypy`
  PASS for every service including `organization-service` and
  `compliance-service`, Python tests 2659 passed / 4 skipped / 0 failed,
  TypeScript package tests 3 passed, frontend tests 11 passed, Next.js
  production build PASS. Overall: all checks passed. The runner output is
  archived at `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log`.
  `REPOSITORY_VERSION` stays `0.9.0` and `CANON_VERSION` stays `0.7.0`;
  the canon document is byte-identical. This records verification only —
  not production readiness, deployment or legal activation.

## [0.8.0] - organization & regional scope context (implementation)

### Added

- A new, independent, in-memory-backed service, `organization-service`
  (CLAUDE-PACK-08 IMPLEMENTATION ROUND, "Organization & Regional Scope
  Context"), with its own `README.md`, `pyproject.toml`, `src/`,
  `tests/`, storage interfaces, and in-memory reference adapters —
  implementing canon 0.7.0 section 19e and ADR-032 through ADR-037
  (all `accepted`) with no further canon edit. Sole authoritative owner
  of `Organization`, `OrganizationalUnit`, `CivicSpace` (first real
  implementation in this repository), `OrganizationalRelation`,
  `OrganizationalHierarchyOverlapPolicy`,
  `OrganizationalInheritancePolicy`, `OrganizationalAuthority`, and the
  reusable `OrganizationalScope` value shape.
- Organization lifecycle: create/activate/suspend/dissolve/rename,
  reorganization (merge/split/declare-successor) with a hard
  no-automatic-role/authority/access-transfer invariant
  (`assert_successor_transfer_has_own_decision`), effective dating
  (`valid_from`/`valid_until`/`recorded_at`/`supersedes`, deterministic
  current/historical/future-dated queries).
- `OrganizationalRelation`: nine relation types across three derived
  categories (hierarchy/continuity/cooperation); deterministic
  hierarchy-cycle detection (`would_create_hierarchy_cycle`) and
  temporary-supervision-cycle detection
  (`would_create_supervision_cycle`); policy-gated overlap validation
  (`OrganizationalHierarchyOverlapPolicy`); territorial reassignment;
  a derived, non-authoritative `parent_reference` read model
  (`recompute_parent_reference`, never itself a source of truth).
- Regional scope authorization (canon 19e.12): a default-deny, pure,
  side-effect-free atomic capability check
  (`check_regional_scope_access`) implementing all six access modes
  (exact/ancestor/descendant-scope, delegated cross-scope via the new
  `ScopeDelegationGrant` reference entity, temporary supervision,
  institutional oversight without data access); inheritance-policy
  ownership (`OrganizationalInheritancePolicy`, restrict-never-broaden);
  a separate, explicit grant/revocation recording step
  (`record_regional_scope_access_grant`/
  `record_regional_scope_access_revocation`) that emits
  `regional_scope_access.granted`/`.revoked` only for modes 2–5.
- Temporary supervision (canon 19e.14): mandatory `valid_from`/
  `valid_until`, a 90-day default maximum
  (`TEMPORARY_SUPERVISION_DEFAULT_MAX_DAYS`), rejection of open-ended
  windows, extension only through a new governed decision with its own
  audit record (`extend_temporary_supervision`).
- Institutional authority (canon 19e.15–19e.17): `OrganizationalAuthority`
  with canon's own exact field names (`role_code`/`scope`, not
  `authority_type`/four separate scope fields — the same reconciliation
  ADR-037 itself performed); self-assignment rejection; the eight-rule
  role-incompatibility baseline (`PAIRWISE_INCOMPATIBLE_ROLES`, version
  `"1.0"`, versioned/extensible); dual-control enforcement (`proposed`
  status plus a distinct-actor `activate_organizational_authority`
  step); expired/revoked/suspended-authority rejection
  (`assert_authority_usable`).
- Thirteen canonical events (canon 20.5/19e.20): `organization.created`
  (first real implementation) plus `organization.activated`/
  `.suspended`/`.dissolved`/`.merged`/`.split`/`.successor_declared`,
  `organizational_relation.created`/`.ended`,
  `organizational_authority.assigned`/`.revoked`,
  `regional_scope_access.granted`/`.revoked` — minimum-necessary payload
  only, no global user identifiers, no unrelated identity data.
- Ten canon section 24 reason codes (`ORGANIZATION_NOT_ACTIVE` through
  `HISTORICAL_SCOPE_NOT_EFFECTIVE`) plus 22 narrowly-necessary additive
  implementation reason codes (audit/event bookkeeping, dual-control and
  self-assignment guards, temporary-supervision window/extension guards)
  — `contracts/reason-codes/pack-08.yml`, 32 entries total.
- Five new entity JSON Schemas (`organization`, `organizational-unit`,
  `civic-space`, `organizational-relation`, `organizational-authority`)
  and seven new event-payload JSON Schemas under `contracts/schemas/`/
  `contracts/events/`; `contracts/openapi/pack-08.yaml` (nine minimal
  reference operations, per this round's own "minimal reference APIs
  only" instruction — organization lifecycle-transition commands and
  OrganizationalUnit management are deliberately not exposed as HTTP
  paths, mirroring PACK-05's own bootstrap-seed precedent).
- `docs/packs/PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md`: the complete,
  per-`role_code` enumeration `docs/packs/PACK-08-MIGRATION-MATRIX.md`
  section 2.3 (OD-11) required before any migration touching
  `RoleAssignment.scope_id` could begin — all 12 `role_code` values
  found in the repository classified against the six-category scheme,
  none migration-blocked (`oversight_reviewer` carries a documented dual
  classification, `observer` a documented not-yet-load-bearing note,
  neither an unresolved ambiguity). Closes OD-11 fully.
- `docs/packs/PACK-08-IMPLEMENTATION.md`,
  `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md`.

### Changed

- `REPOSITORY_VERSION`: `0.7.0 → 0.8.0`
  (`packages/python/epd2-core/src/epd2_core/version.py`,
  `packages/typescript/epd2-types/src/version.ts`, both
  version-consistency unit tests updated). `CANON_VERSION` unchanged at
  `0.7.0` — no canon-owned file was touched this round; `sha256sum
docs/canonical/TZ-00-domain-event-canon.md` still returns
  `a16341a66ce39514e6d8cd6d7a6dde8fc37b0430e3e9ddd7bfd284b116cb9072`,
  confirmed unchanged.
- `docs/canonical/canon-version.json`: `repository_compatibility` upper
  bound widened `<0.8.0 → <0.9.0`.
- `docs/architecture/data-ownership.md`: `Organization`/`CivicSpace`
  rows updated from "Not implemented" to "Implemented (PACK-08)"; new
  rows added for `OrganizationalUnit`/`OrganizationalRelation`/
  `OrganizationalHierarchyOverlapPolicy`/
  `OrganizationalInheritancePolicy`/`OrganizationalAuthority`.
- `tests/repository/test_service_boundaries.py`: new
  `PACK08_SERVICE_PACKAGES` (`organization-service`, the one wholly new
  PACK-08 service) plus positive-assertion boundary tests confirming it
  depends on no other service this round and no other service depends on
  it.
- `tests/contract/_schema_helpers.py`, `test_reason_codes_registry.py`,
  `test_openapi_contract.py`: extended with PACK-08's own registry/
  contract constants and checks, following the PACK-04/05/06/07
  single-service exact-tag-match precedent.
- `tests/contract/test_ct00_01_pack08_schema_validation.py`: new file
  (mirroring the `test_ct00_01_pack07_schema_validation.py` precedent of
  a dedicated file per schema-heavy pack).
- `scripts/check_repository.py`: `REQUIRED_PATHS` extended with every
  file above, plus this round's own `docs/packs/PACK-08-*.md`/
  `docs/handover/PACK-08-*.md` entries (the PACK-07/ADR-026–037/
  `docs/packs/` entries from earlier rounds were not previously present
  in `REQUIRED_PATHS` and are a pre-existing gap this round does not
  retroactively backfill — see the implementation report).

### Verified

- **Local, honest self-report only — no external GitHub Actions run was
  performed or is claimed for this implementation round.** Full detail:
  `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md`.

## [0.7.0] - participation & membership context (implementation)

### Added

- A new, independent, in-memory-backed service, `membership-service`
  (CLAUDE-PACK-07, "Participation & Membership Context"), with its own
  `README.md`, `pyproject.toml`, `src/`, `tests/`, storage interfaces,
  and in-memory reference adapters, plus in-place extensions to the two
  pre-existing PACK-02 services `eligibility-service` and
  `identity-service` — implementing exactly the canon 0.6.0 section 19d
  text and ADR-026 through ADR-031 (all `accepted`) with no further
  canon edit.
- `eligibility-service`: `ParticipantEligibilityPolicy` and
  `ProcessEligibilityPolicy` (canon 19d.4/19d.5), each a versioned,
  activatable critical policy with the shared four-gate activation rule
  (canon 19d.7: approved `GovernanceDecision`, multi-person approval,
  signed policy digest, transparency-log commitment); the four
  separated electoral-eligibility claims (canon 19d.3) computed by
  `evaluate_process_eligibility_claims`, replacing the generic
  `electoral_eligibility_met` concept everywhere; `StepUpAuthenticationRequirement`
  and its fail-closed `check_step_up_requirement` evaluation (canon
  19d.8); `DigitalDecision`/`AssemblyDecision` and the formal-confirmation
  lifecycle (canon 19d.12: `DigitalDecision → FormalConfirmationRequired
→ AssemblyDecision → Confirmed | Rejected | ReturnedForRevision`, with
  a required `divergence_explanation` whenever the final legal decision
  diverges from the digital result, and no silent-approval timeout);
  `AtomicCapabilityResult`/`check_atomic_capability` and scoped
  capability-token issuance (canon 19d.14) via the narrow
  `epd2_credential_service.application.issue_participation_credential`
  read (ADR-027) — `ParticipationRightsProfile` itself stays internal,
  derived, non-authoritative, and non-persisted throughout.
- `membership-service`: `PartyMembershipEligibilityPolicy` (canon 19d.6,
  structurally separate from `ParticipantEligibilityPolicy`, sharing its
  lifecycle plus `incompatibility_rules`/`membership_duration_rules`);
  `MembershipApplication`'s six-state lifecycle (canon 19d.9:
  `application_pending → eligibility_review → human_decision_pending →
approved → rejected → activated`), with Stage A
  (`evaluate_membership_application_eligibility`) _always_ landing on
  `human_decision_pending` regardless of its own recommendation, and
  Stage B (`record_membership_human_decision`) the only path to
  `approved`/`rejected` — each requiring an externally-verified
  `decision_authority_reference`; `activate_membership` as the _only_
  function in the service that ever constructs an `active`
  `Membership` row, layered without overloading `Membership.membership_status`
  (canon 8.3, unchanged, first real implementation); `AffiliationDeclaration`
  (canon 19d.10, immutable/versioned, `declared_reference` an opaque
  reference never a free-text organization name); `ConflictAssessment`
  (canon 19d.11, `decision_authority_reference` mandatory once
  `resolved_incompatible`, enforced fail-closed at construction); the
  polymorphic `Appeal` model reused (a documented, tested duplicate of
  `epd2_moderation_service.domain.Appeal` — no separate `MembershipAppeal`
  was needed, so no new ADR was required per required scope item 9).
- `identity-service`: `AuthenticationContext` (canon 19d.8) and
  `record_step_up_completion`; `IdentityRecord` (7.3) gains eight new
  fields (`date_of_birth`, `citizenship_status`, `residence_status`,
  `identity_assurance_level`, `identity_scheme`,
  `attribute_verification_level`, `attribute_verified_at`,
  `attribute_valid_until`) — all-`None`/empty/`none`-default, backward
  compatible; the two narrow ADR-027 cross-pack reads
  `get_identity_participation_claims`/`check_authentication_step_up_satisfied`.
- Canon 19d.16's hard human-control invariant (no automated process may
  finally decide membership rejection/suspension/expulsion/incompatibility/
  denial of fundamental rights/restoration denial) is structurally
  enforced, not just documented: every consequential membership/conflict
  outcome requires an externally-verified `decision_authority_reference`,
  proven end-to-end in `services/membership-service/tests/test_application.py`
  (`test_stage_a_always_transitions_to_human_decision_pending_regardless_of_recommendation`,
  `test_activate_membership_is_the_only_path_to_active_status`,
  `test_record_conflict_decision_requires_decision_authority_when_incompatible`).
- Membership disclosure restricted by default (ADR-030 item 5): no
  application/status/rejection/suspension/termination/affiliation/conflict
  evidence is exposed on any wire event payload — proven structurally in
  `tests/contract/test_ct00_08_identity_leakage.py`'s new PACK-07
  section (eight tests, one per restricted field/entity).
- The ADR-027 cross-service edge matrix, all `.application`-only:
  `eligibility-service → {identity-service, membership-service,
governance-service, credential-service}`,
  `membership-service → {identity-service, eligibility-service,
governance-service}` — enforced by seven new/extended AST-based tests
  in `tests/repository/test_service_boundaries.py`, and three
  deliberately-duplicated (never imported) logic pieces — the four-gate
  critical-policy activation gate, the polymorphic `Appeal` entity, and
  the step-up assurance-evaluation logic — proven byte-for-byte
  equivalent across their service copies by the new
  `tests/repository/test_pack07_duplicated_logic_parity.py`.
- `contracts/openapi/pack-07.yaml` (tags `eligibility-service`/
  `membership-service`; the four ADR-027 narrow cross-pack reads
  deliberately have no HTTP-shaped path), `contracts/reason-codes/pack-07.yml`
  (38 entries, including the four separated-electoral-eligibility-claim
  codes and four membership human-control codes required scope item 15
  names explicitly). Ten new entity JSON Schemas
  (`participant-eligibility-policy`, `process-eligibility-policy`,
  `step-up-authentication-requirement`, `digital-decision`,
  `assembly-decision`, `party-membership-eligibility-policy`,
  `membership`, `membership-application`, `affiliation-declaration`,
  `conflict-assessment`) and twelve new event-payload JSON Schemas (the
  thirteenth named event, `EligibilityEvaluated`, reuses PACK-02's
  existing schema unchanged), all validated against real,
  directly-constructed domain instances in the new
  `tests/contract/test_ct00_01_pack07_schema_validation.py`.
  `contracts/schemas/identity-record.schema.json` updated to add canon
  19d.2's eight additive fields to `required`/`properties` (the one
  real, pre-existing contract-test gap this round found and fixed).
- `tests/contract/test_ct00_02_unknown_status.py` through
  `test_ct00_09_vote_linkability.py` each extended with a PACK-07
  section as applicable (19 new unknown-status/type `parse_*` cases
  across both services' 12 new enums; 12 forbidden-transition cases;
  event-idempotency and unsupported-event-version checks for
  representative commands from both services; missing-permission and
  audit-creation checks across both services' command surfaces; the
  eight identity-leakage proofs named above; an AST-based import scan
  confirming neither PACK-07 service imports voting/tally/delegation
  domain code, plus a direct-construction proof that
  `ProcessEligibilityClaims`/`MembershipLayerClaims` carry no
  vote/ballot-linkable field). CT-00-11 (AI Human Control) and CT-00-12
  (Emergency Stop) are explicitly documented not-applicable for this
  pack (required scope item 19 excludes new AI-processing functionality
  and no `EmergencyAction` exists in scope) — extending
  `test_ct00_12_emergency_stop_not_applicable.py`'s historical
  not-applicable list a fourth/fifth time. CT-00-10 (Rule Freeze) is
  also documented not-applicable, honestly reporting one related gap
  rather than glossing over it: canon 19d.7's `CriticalPolicyVersionFrozenError`
  is declared in both services' `exceptions.py` for forward
  compatibility but deliberately never raised this round — enforcing it
  needs a persisted Process/Election lifecycle-tracking aggregate this
  pack does not introduce (see that exception class's own docstring).
- One genuine, pre-existing production bug found and fixed via this
  round's own contract-test work (not present in any external report):
  `epd2_membership_service.events.conflict_assessment_state_payload`
  (documented as a "full, canonically-hashable snapshot ... used for
  Audit Core's `after_hash`") was silently missing three of
  `ConflictAssessment`'s thirteen fields (`evidence_references`,
  `supersedes_conflict_assessment_id`, `re_evaluation_due_at`) — those
  three fields were outside Audit Core's tamper-evidence hash. Fixed to
  cover all thirteen fields.
- `REPOSITORY_VERSION` `0.6.0 → 0.7.0` (`packages/python/epd2-core/src/
epd2_core/version.py`, `packages/typescript/epd2-types/src/version.ts`,
  both version-consistency unit tests, and `docs/canonical/canon-
version.json`'s `repository_compatibility` upper bound widened to admit
  it). `CANON_VERSION` is unchanged (`0.6.0`) — this round implements the
  already-accepted canon 19d text; no further canon edit was made.
  `packages/typescript/epd2-types` deliberately gains no PACK-07 domain
  types — this shared package has held "no business logic" (only
  version constants) as an explicit, unbroken architectural boundary
  since PACK-01, honored here rather than overridden; canon
  cross-language contract parity is carried entirely by the JSON
  Schemas and OpenAPI spec named above, exactly as it has been for
  PACK-02 through PACK-06.
- `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`.

### Verified

- **External GitHub Actions run: PASS.** Real network access, real
  dependency installation. Exact results: all 402 required paths present;
  no forbidden paths; version consistency passed; Ruff formatting (359
  files already formatted) and lint passed; Prettier passed; ESLint
  passed; mypy passed for all services; Python 2028 passed / 4 skipped /
  0 failed; TypeScript 3/3 passed; frontend 2/2 passed; Next.js 15.5.21
  production build passed. This closes out PACK-07 implementation as a
  genuine external PASS, not a local self-report.
- Full local verification suite also run in this repository's sandboxed,
  network-restricted environment during implementation (see
  `LOCAL_VERIFICATION.md`): Ruff (lint + format) clean; mypy clean
  per-service and for `packages/python/epd2-core`/`scripts`/
  `tests/repository`/`tests/contract` (run separately per the
  `Makefile`'s own documented `--import-mode=importlib` limitation); the
  complete Python test suite passing (2020 passed, 5 skipped — the
  `hypothesis`-unavailable skip and cache-related forbidden-paths check
  that the external, clean-checkout run above doesn't hit), including
  PACK-07's own `tests/contract`/`tests/repository` additions, using the
  standalone-`pytest`/`PYTHONPATH` workaround `LOCAL_VERIFICATION.md`
  documents. TypeScript/Prettier/frontend-build verification was
  unavailable in this sandbox alone (no network access to install
  `npm`/`prettier`/Next.js toolchain dependencies) — that gap is exactly
  what the external GitHub Actions run above closes. Full detail,
  including every command's literal output and the external PASS
  results: `docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`.

## [Unreleased] - canon minor version 0.6.0 (Participation & Membership Context)

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.5.0 →
0.6.0` (ADR-026 through ADR-031, all `accepted`, no further amendment)
  — the fifth edit to this document's own text since its original
  acceptance (after ADR-010's `0.1.0 → 0.2.0`, ADR-013's `0.2.0 →
0.3.0`, ADR-018/ADR-020's `0.3.0 → 0.4.0`, and ADR-023/ADR-025's `0.4.0
→ 0.5.0`). Adds a new section 19d ("Участие и членство / Participation
  & Membership Context"), inserted between sections 19c and 20, the same
  non-renumbering technique used for 19a/19b/19c. Ten new canonical
  entities: `ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
  `StepUpAuthenticationRequirement`, `DigitalDecision`,
  `AssemblyDecision` (owner: Eligibility Engine, i.e. `eligibility-service`,
  extended for the first time since PACK-02); `PartyMembershipEligibilityPolicy`,
  `AffiliationDeclaration`, `ConflictAssessment`, `MembershipApplication`
  (owner: Membership Service, i.e. the new `membership-service`);
  `AuthenticationContext` (owner: Identity Verification Service, i.e.
  `identity-service`, extended). `IdentityRecord` (7.3) gains eight new
  fields (`date_of_birth`, `citizenship_status`, `residence_status`,
  `identity_assurance_level`, `identity_scheme`,
  `attribute_verification_level`, `attribute_verified_at`,
  `attribute_valid_until`); its existing ten fields are unchanged. The
  generic `electoral_eligibility_met` concept — never itself a canonical
  field — is replaced everywhere by four separated claims
  (`active_electoral_eligibility_met`, `passive_electoral_eligibility_met`,
  `party_internal_voting_eligibility_met`,
  `party_office_candidacy_eligibility_met`). `MembershipApplication`'s
  six-state lifecycle (`application_pending`, `eligibility_review`,
  `human_decision_pending`, `approved`, `rejected`, `activated`) is
  layered on top of, without overloading, `Membership.membership_status`
  (8.3), which keeps all eight existing fields, seven existing status
  values, and its owner unchanged. `AffiliationDeclaration` gains five
  temporal/verification fields (`valid_from`, `valid_until`,
  `verification_status`, `verified_at`, `verified_by`).
  `ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`,
  `PartyMembershipEligibilityPolicy`, and `StepUpAuthenticationRequirement`
  are classified as "critical policies," each gaining
  `signed_policy_digest_reference`/`transparency_log_commitment_reference`
  and a four-independent-gate activation rule (verified
  `GovernanceDecision`, `multi_person_approval_met`, signed digest,
  transparency-log commitment) plus a policy-freeze rule extending
  CT-00-10. `ProcessEligibilityPolicy` also carries seven legal-effect
  fields (`decision_effect`, `formal_confirmation_required`,
  `formal_confirmation_authority`, `secret_ballot_required`,
  `permitted_participation_mode`, `required_assurance_level`,
  `accessibility_profile`) and the `DigitalDecision → AssemblyDecision`
  formal-confirmation lifecycle. `ParticipationRightsProfile` is
  characterized as an internal, non-authoritative, never-stored derived
  model; the only two permitted enforcement mechanisms anywhere in this
  context are an atomic capability check or a single-purpose scoped
  capability token. `Appeal` (14.3) gains a documentation clarification
  only (`decision_id` as a polymorphic target reference, a standing
  default for any future appealable decision type) — no field, status,
  or owner change. The consequential-human-control hard invariant widens
  to a seventh, open-ended category (denial of a fundamental member
  right, however produced). `DomainPseudonymReference`,
  `AntiCorrelationInvariant`, and `CryptographicProtocolProfile` are
  named with their governing invariants stated (the latter's gate now
  nine items, adding timing/transport unlinkability and
  privacy-preserving revocation) but not defined as fully fielded
  entities, deferred to future implementing ADRs. A future
  architectural requirement for consequential AI-generated summaries
  (deterministic source-reference mapping, coverage metadata, human-
  review status, immutable `AIProcessingRecord` linkage) is recorded by
  reference only — `AIProcessingRecord` (17.1, 19c) itself is not
  modified. Section 20 gains a new event catalog subsection (20.16) and
  three completing `Membership` (20.5) event names
  (`membership.terminated`, `.rejected`, `.expired`). Section 22 gains
  ten new ownership-matrix rows; section 23 gains new forbidden-link
  entries. `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py`, and
  `packages/typescript/epd2-types/src/version.ts` updated to match, with
  both version-consistency unit tests updated and
  `scripts/verify_versions.py` passing; `REPOSITORY_VERSION` is
  unchanged (`0.6.0`) since no `membership-service` or
  `eligibility-service` extension code exists yet — this is a canon-only
  change, per CLAUDE-PACK-07's own governance round (`docs/adr/ADR-026`
  through `ADR-031`, all `accepted`; `docs/review/PACK-07-OWNER-DECISIONS.md`).
- `docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md`.

### Verified

- **PACK-07 canon round PASS**, confirmed by a complete external GitHub
  Actions run with real network access: 1822 Python tests passed, 3
  skipped (the same genuine CT-00-10/CT-00-12 not-applicable markers as
  the PACK-06 PASS baseline above — this canon-only round touched no
  test file besides the two version-consistency unit tests, which
  pass), TypeScript tests passed (3/3), frontend tests passed (2/2), a
  successful Next.js production build, and Prettier, Ruff, ESLint, and
  mypy all clean, with all 363 required paths present and no forbidden
  files. See `docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md` (§7) for
  the full breakdown, including reconciliation against this sandbox's
  own local run (1815 passed, 4 skipped — `hypothesis` cannot be
  installed here, so its one property-based test module import-skips
  as a single unit instead of running its seven tests individually).
  This is a canon/ADR-acceptance PASS only — no `membership-service`/
  `eligibility-service` implementation PASS is claimed; that remains a
  distinct, future implementation round.

## [Unreleased] - canon minor version 0.5.0 (AI Processing Context)

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.4.0 →
0.5.0` (ADR-023 and ADR-025, both accepted with amendments) — the
  fourth edit to this document's own text since its original acceptance
  (after ADR-010's `0.1.0 → 0.2.0`, ADR-013's `0.2.0 → 0.3.0`, and
  ADR-018/ADR-020's `0.3.0 → 0.4.0`). Adds a new section 19c ("ИИ-
  обработка — расширение / AI Processing Context"), extending the
  already-existing section 17 (`AIProcessingRecord`, unchanged twelve
  fields and six-value `human_review_status`) rather than defining a new
  entity. Adds a new, independent `processing_status` field
  (`requested`/`input_prepared`/`processing`/`completed`/`failed`/
  `rejected_by_policy` — deliberately no stored `superseded` value) kept
  structurally separate from `human_review_status`; a unified
  `supersedes_ai_processing_record_id` field generalizing
  `GovernanceDecision.supersedes_decision_id`'s derived-supersession
  pattern to cover both a superseded processing run and a superseded
  review outcome; fifteen further fields (model/deployment governance,
  provenance/integrity, confidence/uncertainty, explainability,
  human-reviewer provenance, lifecycle timestamps); a new
  `redaction_manifest` embedded, immutable value object (nine sub-
  fields: `redaction_policy_reference`, `redaction_policy_version`,
  `input_classification`, `checked_field_categories`,
  `removed_field_categories`, `prepared_input_hash`, `validator_version`,
  `validated_at`, `result`) replacing what would otherwise have been a
  flat `redaction_policy_reference`/`redaction_applied` field pair; three
  disclosure-lifecycle fields (`disclosure_required`,
  `disclosure_package_reference`, `disclosure_receipt_reference`) plus a
  derived, non-stored `DisclosureStatus` read-model type
  (`not_required`/`pending_package`/`pending_publication`/`published`),
  mirroring `GovernanceDecision`/`FinalityStatus`'s own stored-vs-derived
  split; and `AIDisclosurePackage`, defined explicitly as a contract/
  value object — never a canonical system-of-record entity, never
  persisted by either `ai-processing-service` or `transparency-service`,
  its only durable trace being the resulting `PublicLedgerEntry` row
  (already canon, 19a.1, owned by `transparency-service`, unchanged) plus
  the two opaque reference fields on `AIProcessingRecord`. A mandatory,
  explicit five-step disclosure protocol is recorded (19c.7): verified
  human approval, immutable `AIDisclosurePackage` creation,
  `transparency-service` publication through its existing
  `publish_ledger_entry` path, receipt recording, and fail-closed
  finalization gating on `DisclosureStatus = published`. Section 20.12's
  AI event catalog is corrected (`ai.output.corrected` →
  `ai.output_corrected`) and expanded with six new events. Section 22's
  ownership matrix gains no new row (`AIProcessingRecord`'s existing "AI
  Accountability Service" ownership is unchanged; `redaction_manifest`
  and `AIDisclosurePackage` are, respectively, an embedded value object
  and a contract/value object, not separately owned entities). Section
  23's forbidden-links list gains new entries covering no-autonomous-
  decision, no-identity-reverse-lookup, no-vote-linkage-reconstruction,
  no-model-provider-mutation-authority, no-raw-private-input-in-
  disclosure, and no-hidden-reasoning-claim invariants.
  `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py`, and
  `packages/typescript/epd2-types/src/version.ts` updated to match, with
  both version-consistency unit tests updated and
  `scripts/verify_versions.py` passing; `REPOSITORY_VERSION` is
  unchanged (`0.5.0`) since no `ai-processing-service` code exists yet —
  this is a canon-only change, per CLAUDE-PACK-06's own governance round
  (`docs/adr/ADR-021` through `ADR-025`, all `accepted`;
  `docs/review/PACK-06-OWNER-DECISIONS.md`).

## [0.6.0] - AI processing context (implementation)

### Added

- A new, independent, in-memory-backed service, `ai-processing-service`
  (CLAUDE-PACK-06, "AI Processing Context"), with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interfaces, model-provider
  and redaction-validator abstractions, and in-memory reference adapters,
  implementing exactly the canon 0.5.0 section 19c text and ADR-021
  through ADR-025 (all `accepted`) with no further canon edit.
- The one canon entity this pack owns, `AIProcessingRecord` (canon 17.1,
  extended by 19c), with two independent, structurally separate status
  planes: `processing_status` (`requested -> input_prepared -> processing
-> {completed | failed | rejected_by_policy}`, `rejected_by_policy`
  also directly reachable from `requested`; no stored `superseded` value)
  and `human_review_status` (canon's unchanged six-value enum; `superseded`
  is never directly stored, only ever surfaced by the derived
  `derive_effective_human_review_status` read model, mirroring
  `GovernanceDecision`/`FinalityStatus`'s own stored-vs-derived split).
  Both statuses' `superseded` meaning route through one shared field,
  `supersedes_ai_processing_record_id`. The embedded, immutable
  `RedactionManifest` value object (nine fields) and the
  `AIDisclosurePackage` contract/value object (never persisted by either
  `ai-processing-service` or `transparency-service` — its only durable
  trace is the resulting `PublicLedgerEntry` row plus two opaque
  reference fields on `AIProcessingRecord`) are both implemented exactly
  per canon 19c.4/19c.6.
- Fifteen application-layer commands (`request_ai_processing`,
  `prepare_input`, `begin_processing`, `complete_processing_with_provider`,
  `fail_processing`, `reject_processing_by_policy`, `review_ai_output`,
  `supersede_ai_processing_record`, `assert_consequential_output_reviewed`,
  `create_disclosure_package`, `publish_ai_disclosure`,
  `assert_disclosure_complete_for_official_finalization`,
  `get_ai_processing_record`, `get_disclosure_status`,
  `get_effective_human_review_status`), each with `epd2_audit_core` audit
  entries, CT-00-04 idempotency where applicable, and eleven canonical AI
  events (canon section 20.12, corrected `ai.output.corrected` ->
  `ai.output_corrected`, plus six new events).
- `human_review_status` decided exactly once, at `request_ai_processing`
  (`pending` if `is_consequential`, else `not_required`); silence,
  timeout, a missing reviewer, or missing role verification never imply
  approval — every consequential output can finish only through an
  explicit `approved`/`approved_with_changes`/`rejected` outcome recorded
  by `review_ai_output`.
- Fourteen named fail-closed conditions (model unavailable, timeout,
  malformed output, unsupported model version, low confidence, policy
  conflict, redaction failure, prompt-injection signal, prohibited data,
  missing human reviewer, invalid reviewer role, reviewer scope mismatch,
  unverified input provenance, missing required disclosure), each mapped
  to its own registered reason code and exercised end-to-end.
- The narrow governance read dependency (ADR-022):
  `epd2_governance_service.application.verify_role_assignment_for_action`,
  returning only `authorized`/`verified_actor_reference`/
  `verified_scope_reference`/`reason_code` — the sole function
  `ai-processing-service` ever imports from `governance-service`, enforced
  by an AST-based contract test. Four reviewer roles
  (`ai_output_reviewer`, `ai_moderation_reviewer`, `ai_governance_reviewer`,
  `ai_publication_reviewer`), purpose/scope-specific authorization, and
  self-review prohibition for moderation/governance/ballot-adjacent/
  official-publication uses.
- Six closed use classes (`summarization`, `classification`,
  `recommendation`, `drafting`, `anomaly_indication`,
  `policy_compliance_assistance`) with closed `purpose_code`/`target_type`
  allow-lists (ADR-025 §2) — `anomaly_indication`'s allow-list contains no
  vote/ballot-linked `target_type` at all, structurally preventing AI
  processing from ever reconstructing vote linkage.
- A provider abstraction (`AIModelProvider` Protocol: `submit`/`cancel`
  only, no callback/tool/command parameter of any kind, so a model
  provider structurally cannot mutate Civic OS) and a redaction-validator
  abstraction (`RedactionValidator` Protocol), both with scripted test
  doubles. External providers are forbidden for voting/tally/
  participation-pattern/credential/identity/governance-sensitive/
  unrestricted-audit data and for `anomaly_indication` (self-hosted
  required); unknown `processing_region`/`data_retention_mode` is
  fail-closed.
- The mandatory five-step disclosure protocol (ADR-025 §5, canon 19c.7):
  verified approval, immutable `AIDisclosurePackage` creation,
  `transparency-service` publication through its existing
  `publish_ledger_entry` (never a direct transparency-storage write by
  this service), receipt recording, and fail-closed finalization gating
  on `DisclosureStatus = published`.
- `contracts/openapi/pack-06.yaml` (tag `ai-processing-service`;
  `verify_role_assignment_for_action` deliberately has no HTTP-shaped
  path), `contracts/reason-codes/pack-06.yml` (29 entries: 4 generic/canon,
  15 from the PACK-06 spec, 7 additive per ADR-024, 1 this service's own
  duplicate-conflict code, plus 1 audit-classification code and 1
  governance-owned code registered here purely for this file's own
  completeness, following the same cross-pack duplication precedent
  `PERMISSION_DENIED` already uses). Two entity JSON Schemas
  (`ai-processing-record`, `ai-disclosure-package`) and one event-payload
  JSON Schema, all validated against real generated payloads.
- `tests/repository/test_service_boundaries.py` extended with seven new
  PACK-06 boundary tests (no PACK-06-to-PACK-06 cross-service import, no
  other service imports PACK-06, PACK-06 calls only the ADR-022/ADR-025-
  named upstream applications, PACK-06 never imports the excluded
  identity/account/credential/eligibility/initiative/deliberation/
  moderation/delegation/voting/tally services, and the governance-service
  and transparency-service edges are each restricted by an AST-based
  scan to exactly one named function).
- `tests/contract/test_ct00_01_schema_validation.py` through
  `test_ct00_09_vote_linkability.py` each extended with a PACK-06 section
  as applicable (schema validation and unknown-`processing_status`/
  `human_review_status` rejection; the two new `parse_processing_status`
  and `parse_human_review_status` functions and their
  `UnknownProcessingStatusError`/`UnknownHumanReviewStatusError`
  exceptions newly added to `domain.py`; forbidden-transition cases for
  both status planes; event idempotency, unsupported-event-version, and
  audit-creation checks for `request_ai_processing`; the flagship
  self-review-prohibition authorization test for `review_ai_output`;
  structural schema/OpenAPI/event-payload identity- and vote-leakage
  checks; a direct-construction proof that no `anomaly_indication`
  target type is vote/ballot-linked; and an AST-based import scan
  confirming `ai-processing-service` never imports voting/tally/
  delegation/account/identity/credential service code at all). CT-00-11
  (AI Human Control) moves from not-applicable to fully and centrally
  passing for the first time, in a new dedicated file,
  `test_ct00_11_ai_human_control.py` (five end-to-end proofs: no review
  at all, silence never implying approval, an explicit rejection, a
  successful approval, and the official-publication path's additional
  published-disclosure requirement). CT-00-10 (Rule Freeze) and CT-00-12
  (Emergency Stop) are explicitly documented not-applicable for this
  pack (required scope item 17); `test_ct00_11_12_not_applicable.py` is
  renamed `test_ct00_12_emergency_stop_not_applicable.py` to reflect
  that CT-00-11 is no longer among the not-applicable markers it
  records.
- `REPOSITORY_VERSION` `0.5.0 → 0.6.0` (`packages/python/epd2-core/src/
epd2_core/version.py`, `packages/typescript/epd2-types/src/version.ts`,
  both version-consistency unit tests, and `docs/canonical/canon-
version.json`'s `repository_compatibility` upper bound widened to admit
  it). `CANON_VERSION` is unchanged (`0.5.0`) — this round implements the
  already-accepted canon 19c text; no further canon edit was made.
- `docs/handover/PACK-06-REPORT.md`.

### Verified

- **PACK-06 PASS**, confirmed by a complete external GitHub Actions run
  with real network access: 1822 Python tests passed, 3 skipped
  (genuine CT-00-10/CT-00-12 not-applicable-in-earlier-packs markers —
  CT-00-11 is no longer among them, now fully applicable and passing
  for PACK-06, section 0 above), TypeScript tests passed (3/3), frontend
  tests passed (2/2), a successful Next.js production build, and
  Prettier, Ruff, ESLint, and mypy all clean, with all 363 required
  paths present and no forbidden files. Three real, externally-found
  gaps were fixed en route to this PASS, each touching exactly one file
  and no implementation logic, schema, canon, or ADR content: a
  six-file Prettier formatting gap (revision 2); a Markdown authoring
  defect in this file's own PACK-06 test-coverage bullet — asterisks
  used as informal wildcard shorthand inside/adjacent to inline code
  spans, plus missing whitespace collapsing distinct words together
  (revision 3); and a stale hardcoded TypeScript version-test literal in
  `version.test.ts` still expecting `CANON_VERSION 0.4.0`/
  `REPOSITORY_VERSION 0.5.0` instead of the correct `0.5.0`/`0.6.0`
  (revision 4). Full detail, including every command's literal output
  and the external run's exact results: `docs/handover/PACK-06-REPORT.md`.

## [Unreleased] - canon minor version 0.4.0 (Governance Context)

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.3.0 →
0.4.0` (ADR-018 and ADR-020, both accepted with amendments) — the third
  edit to this document's own text since its original acceptance (after
  ADR-010's `0.1.0 → 0.2.0` and ADR-013's `0.2.0 → 0.3.0`). Adds a new
  section 19b ("Governance Context") defining three new canonical
  entities — `GovernancePolicy`, `GovernanceDecision`,
  `TechnicalChallenge` — with full fields, identifiers, statuses,
  owners, invariants, allowed transitions, forbidden links, and immutable
  correction/superseding semantics, and fully integrating the
  already-canon-defined `RoleAssignment` (8.4, unchanged) as the
  authority reference every new entity relies on; a new section 20.15
  with the twelve-event Governance canonical event catalog; three new
  section 22 ownership-matrix rows; and section 23 forbidden-link
  entries reworded (the undefined `AdministratorRole` reference
  generalized to any `RoleAssignment` regardless of `role_code`) and
  extended for the three new entities. `GovernanceDecision`'s stored
  status enum is exactly `proposed`/`approved`/`rejected` (no stored
  `superseded` value; corrections use `supersedes_decision_id`,
  superseded-ness is derived at query time); `finality_outcome` stores
  only `final`/`invalidated`, with a separate four-value `FinalityStatus`
  read-model type (`provisional`/`finality_blocked`/`final`/
  `invalidated`) documented as a query/read-model, not a stored field.
  `TechnicalChallenge` uses `submitter_authorization_type`
  (`participation_credential`/`role_assignment`) plus an opaque
  `submitter_authorization_reference`, never a mandatory
  `RoleAssignment`-only reference. The accepted cross-pack write
  boundary (ADR-017) is recorded as its own subsection (19b.6):
  `voting-service` remains the sole writer of `Ballot`; `governance-service`
  never mutates `Ballot` or `ResultPublication` storage; result finality
  is represented and queried entirely through `governance-service`.
  Transparency Context (19a), AI-processing (section 17), and
  Emergency/Crisis Override (section 19) remain explicitly untouched and
  unimplemented by this addition (19b.7). `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py`, and
  `packages/typescript/epd2-types/src/version.ts` updated to match, with
  both version-consistency unit tests updated and
  `scripts/verify_versions.py` passing; `REPOSITORY_VERSION` is unchanged
  (`0.4.0`) since no `governance-service` code exists yet — this is a
  canon-only change, per CLAUDE-PACK-05's own governance round
  (`docs/adr/ADR-016` through `ADR-020`, all `accepted`;
  `docs/review/PACK-05-OWNER-DECISIONS.md`).

## [0.5.0] - governance context (implementation)

### Added

- A new, independent, in-memory-backed service, `governance-service`
  (CLAUDE-PACK-05, "Governance Context"), with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interfaces, and in-memory
  reference adapters, implementing exactly the canon 0.4.0 section 19b
  text and ADR-016 through ADR-020 (all `accepted`) with no further canon
  edit.
- All four canon 19b entities: `RoleAssignment` (canon 8.4, physically
  relocated into `governance-service` per ADR-016; `role_code` remains an
  open string at canon level, with the closed 8-value pilot taxonomy
  enforced only at the application layer), `GovernancePolicy`,
  `GovernanceDecision` (a single entity with a `decision_type`
  discriminator covering `ballot_invalidation`,
  `technical_challenge_adjudication`, `result_finality_determination`,
  `mandate`, `oversight_directive`; stored status is exactly
  `proposed`/`approved`/`rejected` — no stored `superseded` value,
  corrections use `supersedes_decision_id`), and `TechnicalChallenge`,
  plus the derived, never-stored `FinalityStatus` read model
  (`provisional`/`finality_blocked`/`final`/`invalidated`, a distinct type
  from the stored `finality_outcome`).
- Fourteen application-layer commands (`request_role_assignment`,
  `activate_role_assignment`, `revoke_role_assignment`,
  `get_role_assignment`, `propose_governance_policy`,
  `activate_governance_policy`, `propose_governance_decision`,
  `approve_governance_decision`, `reject_governance_decision`,
  `get_governance_decision`, `is_current_approved_decision`,
  `get_finality_status`, `submit_technical_challenge`,
  `begin_technical_challenge_review`, `get_technical_challenge`), each
  with `epd2_audit_core` audit entries, CT-00-04 idempotency, and the
  twelve canonical Governance events (canon section 20.15).
- Two-actor approval enforced end-to-end (ADR-020 item 1): proposer and
  approver must resolve to distinct `actor_id`s via two active, in-scope
  `RoleAssignment`s, required for `GovernancePolicy` activation, every
  `GovernanceDecision` approval/rejection, ballot invalidation, and
  result-finality determination; no role may approve or grant its own
  assignment (`SAME_ACTOR_APPROVAL_REJECTED`).
- The pilot role taxonomy (`PILOT_ROLE_CODES`, ADR-020 §5):
  `governance_policy_proposer`, `governance_policy_approver`,
  `governance_reviewer`, `technical_challenge_reviewer`,
  `ballot_invalidation_proposer`, `ballot_invalidation_approver`,
  `oversight_reviewer`, `observer`, enforced only where a `RoleAssignment`
  is created or used, never as a canon-level closed enum.
- A deployment-time-only bootstrap seed (`bootstrap.py`,
  `run_bootstrap_seed`): not exposed through the normal API surface,
  creates exactly two distinct-actor initial `RoleAssignment`s, produces
  an immutable, checksummed `BootstrapSeedManifest`, records real
  `AuditEvent`s, and is permanently disabled after its first successful
  execution (`BootstrapAlreadyExecutedError`).
- `TechnicalChallenge` submission and adjudication (canon 19b.4/19b.5):
  eligible participants via a caller-supplied, never-dereferenced
  `participation_credential`-type reference (mirroring PACK-04's
  `publish_ledger_entry` `raw_content` precedent), or authorized
  observers/reviewers via a locally-validated, active, in-scope
  `role_assignment`-type reference; adjudication is always a side effect
  of approving/rejecting the linked `technical_challenge_adjudication`
  `GovernanceDecision`, never a standalone command; finality is blocked
  while any challenge remains `submitted`/`under_review`; a zero-challenge
  result still requires an explicit two-actor
  `result_finality_determination` decision (deadline expiry alone is
  never sufficient).
- Ballot invalidation via the accepted ADR-017 Option B: `voting-service`
  remains the sole writer of `Ballot`, gaining one narrow new command
  (`epd2_voting_service.application.invalidate_ballot`) that verifies an
  approved, correctly-scoped `ballot_invalidation` `GovernanceDecision`
  (read via the new `epd2_governance_service.application.
get_governance_decision`/`is_current_approved_decision`, the first
  bidirectional cross-pack `.application`-only read edge in this
  project) before transitioning `Ballot` to `invalidated`;
  `governance-service` never writes `voting-service` storage directly.
- `contracts/openapi/pack-05.yaml` (17 operations, tag
  `governance-service`; the bootstrap seed command deliberately has no
  HTTP-shaped path at all, per required scope item 6), plus a new
  `invalidateBallot` operation added to `contracts/openapi/pack-03.yaml`
  under the `voting-service` tag. `contracts/reason-codes/pack-05.yml`
  (27 entries: 9 carried forward from the PACK-05 spec, 4 new per
  ADR-019, reused generics, and this service's own additive
  duplicate-conflict/audit-classification codes);
  `BALLOT_INVALIDATION_NOT_AUTHORIZED` independently redeclared in
  `contracts/reason-codes/pack-03.yml` too, since the literal is used by
  a real `voting-service` guard. Four entity JSON Schemas
  (`role-assignment`, `governance-policy`, `governance-decision`,
  `technical-challenge`) and four event-payload JSON Schemas, all
  validated against real generated payloads.
- `tests/repository/test_service_boundaries.py` extended with seven new
  PACK-05 boundary tests (no PACK-05-to-PACK-05 cross-service import, no
  PACK-02/04 service imports PACK-05, only `voting-service` among PACK-03
  may import `governance-service`, that edge is `.application`-only in
  both directions and matches ADR-017, PACK-05 calls only the
  ADR-017-named upstream applications
  `epd2_voting_service.application`/`epd2_tally_service.application`,
  PACK-05 never imports the excluded identity/account/eligibility/
  credential/initiative/deliberation/moderation/delegation/transparency
  services, and `tally-service` never imports `governance-service`).
- `tests/contract/test_ct00_01_schema_validation.py` through
  `test_ct00_10_rule_freeze.py` each extended with a PACK-05 section
  (schema validation for all four entities and their event payloads;
  unknown-status/forbidden-transition parametrized cases for all four
  status enums; event idempotency, unsupported-event-version,
  audit-creation checks for `request_role_assignment`; the flagship
  two-actor authorization test for `activate_governance_policy`; and
  `GovernanceDecision`'s "immutable once approved/rejected" freeze
  invariant). `test_ct00_08_identity_leakage.py` and
  `test_ct00_09_vote_linkability.py` extended with structural schema
  checks, a real end-to-end command call proving `actor_id`/
  `assigned_by`/`*_role_id`/`submitter_authorization_reference` never
  reach a public event payload, an AST-based import scan confirming
  `governance-service` never imports `epd2_delegation_service`/
  `epd2_account_service`/`epd2_identity_service` or
  `epd2_voting_service.domain`/`epd2_tally_service.domain` directly, and
  a direct-construction proof that `GovernanceDecision.subject_reference`
  rejects `vote_envelope_id` (no reverse vote-linkability path).
  `test_ct00_11_12_not_applicable.py` updated to record PACK-05's
  identical AI-processing/Emergency-Override exclusion (required scope
  item 13) alongside PACK-02's and PACK-03's.
- `REPOSITORY_VERSION` `0.4.0 → 0.5.0` (`packages/python/epd2-core/src/
epd2_core/version.py`, `packages/typescript/epd2-types/src/
version.ts`, both version-consistency unit tests, and
  `docs/canonical/canon-version.json`'s `repository_compatibility` upper
  bound widened to admit it). `CANON_VERSION` is unchanged (`0.4.0`) —
  this round implements the already-accepted canon 19b text; no further
  canon edit was made.
- `docs/handover/PACK-05-REPORT.md`.

### Verified

- **PACK-05 PASS**, confirmed by a complete external GitHub Actions run
  with real network access: 1719 Python tests passed, 2 skipped (genuine
  CT-00-11/12 not-applicable markers), TypeScript tests passed (3/3),
  frontend tests passed (2/2), a successful Next.js production build, and
  Prettier, lint, and type checks all clean, with all 336 required paths
  present and no forbidden files. Two real, externally-found Prettier
  gaps were fixed en route (a two-file formatting gap, and a malformed
  Markdown table in `services/governance-service/README.md`) before this
  PASS; neither changed any implementation logic, schema, test, canon, or
  ADR content. Full detail: `docs/handover/PACK-05-REPORT.md`.

## [Unreleased] - canon minor version 0.3.0 (Transparency Context)

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.2.0 →
0.3.0` (ADR-013, accepted with amendments) — the second edit to this
  document's own text since its original acceptance (the first was
  ADR-010's `0.1.0 → 0.2.0`). Adds a new section 19a ("Прозрачность /
  Transparency Context") defining four new canonical entities —
  `PublicLedgerEntry`, `AuditExportPackage`, `DisclosurePolicy`,
  `LobbyLogEntry` — with full fields, identifiers, statuses, owners,
  invariants, forbidden links, and immutable/correction semantics; a new
  section 20.14 with the ten-event Transparency canonical event catalog;
  four new section 22 ownership-matrix rows; and new section 23
  forbidden-link entries covering identity, credential, vote-envelope,
  delegation, private audit payload, and internal role-reference
  exposure. Governance Context (5.12), AI-processing (section 17), and
  Emergency/Crisis Override (section 19) remain explicitly untouched and
  unimplemented by this addition (canon 19a's own closing subsection).
  `docs/canonical/canon-version.json`,
  `packages/python/epd2-core/src/epd2_core/version.py`, and
  `packages/typescript/epd2-types/src/version.ts` updated to match, with
  both version-consistency unit tests updated and
  `scripts/verify_versions.py` passing; `REPOSITORY_VERSION` is unchanged
  (`0.3.0`) since no `transparency-service` code exists yet — this is a
  canon-only change, per CLAUDE-PACK-04's own governance round
  (`docs/adr/ADR-011` through `ADR-015`, all `accepted`;
  `docs/review/PACK-04-OWNER-DECISIONS.md`).

## [0.4.0] - transparency context (implementation)

### Added

- A new, independent, in-memory-backed service, `transparency-service`
  (CLAUDE-PACK-04, "Transparency Context"), with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interfaces, and in-memory
  reference adapters, implementing exactly the canon 0.3.0 section 19a
  text and ADR-011 through ADR-015 (all `accepted`) with no further canon
  edit.
- All four canon 19a entities: `PublicLedgerEntry`, `AuditExportPackage`,
  `DisclosurePolicy`, `LobbyLogEntry` — domain models, `StrEnum` statuses,
  `ALLOWED_TRANSITIONS` state machines where canon defines one
  (`AuditExportPackage`'s `generated -> published -> superseded`,
  `DisclosurePolicy`'s `draft -> active -> superseded`,
  `LobbyLogEntry`'s `submitted -> published`), and permanent
  content-immutability with no transition table at all for
  `PublicLedgerEntry` (a correction is always a new superseding row, per
  canon 19a.1).
- Ten application-layer commands (`publish_ledger_entry`,
  `correct_ledger_entry`, `generate_audit_export_package`,
  `publish_audit_export_package`, `verify_audit_export_package`,
  `define_disclosure_policy`, `activate_disclosure_policy`,
  `submit_lobby_log_entry`, `publish_lobby_log_entry`,
  `correct_lobby_log_entry`), each with `epd2_audit_core` audit entries,
  CT-00-04 idempotency, and the ten canonical Transparency events (canon
  section 20.14).
- Per-field `DisclosurePolicy` rules (`public`/`redacted`/`restricted`/
  `prohibited` classes; missing or ambiguous rules default to
  `prohibited`; prohibited fields cannot be overridden by any rule;
  role-scope generalization uses labels only; a structural
  `FORBIDDEN_FIELD_NAMES` set — identity, account, credential,
  vote-envelope, and internal role-UUID fields — is stripped
  unconditionally before any policy is even consulted); a
  `small_cell_threshold` of `10` for analytics-shaped fields, with
  `ResultPublication` counts explicitly exempt (exact official counts
  remain exact).
- Lobby Log rules: a 7-calendar-day publication deadline
  (`is_within_publication_deadline`), mandatory automated completeness
  and prohibited-field validation on every publish, no mandatory human
  pre-publication approval by default, and corrections only through a
  new superseding entry (`correct_lobby_log_entry`), never a rewrite.
- Public audit export rules (`AuditExportPackage`): a
  `ChainProofItem`-based proof of continuity, ordering, and integrity for
  an exported hash-chain segment (`event_hash`, `previous_event_hash`,
  public-safe metadata, and sequence position per item), a
  package-level `package_digest` and an `integrity_proof`
  signature-shaped field, and an explicit non-claim of full recomputation
  of redacted private `AuditEvent` hashes (`verify_audit_export_package`
  checks the exported segment's own internal consistency only).
- `contracts/openapi/pack-04.yaml` (10 operations, tag
  `transparency-service`), `contracts/reason-codes/pack-04.yml` (18
  entries), four entity JSON Schemas (`public-ledger-entry`,
  `audit-export-package`, `disclosure-policy`, `lobby-log-entry`) and
  four event-payload JSON Schemas, all validated against real generated
  payloads.
- Additive, read-only upstream `.application`-layer functions (ADR-012):
  `epd2_audit_core.application.list_by_target_types` (used directly by
  `generate_audit_export_package`), plus four further sanctioned-but-
  not-yet-called functions (`get_published_initiative`,
  `get_initiative_version`, `get_moderation_decision`, `get_ballot`,
  `get_result_publication`) added to their respective upstream services
  and enforced as PACK-04's only permitted upstream `.application`
  imports by `tests/repository/test_service_boundaries.py`.
- `tests/repository/test_service_boundaries.py` extended with four new
  PACK-04 boundary tests (no PACK-04-to-PACK-04 cross-service import, no
  PACK-02/03 service imports PACK-04, PACK-04 calls only the
  ADR-012-named upstream applications, PACK-04 never imports
  deliberation-service, delegation-service, or the PACK-02 identity
  services).
- `tests/contract/test_ct00_08_identity_leakage.py` and
  `tests/contract/test_ct00_09_vote_linkability.py` extended with a
  PACK-04 section each: structural schema checks that no entity or event
  schema exposes an identity/credential/vote-envelope/role-UUID field,
  and a real end-to-end command call proving a caller-supplied
  vote-envelope-shaped field is dropped before it ever reaches a public
  payload.
- `REPOSITORY_VERSION` `0.3.0 → 0.4.0` (`packages/python/epd2-core/src/
epd2_core/version.py`, `packages/typescript/epd2-types/src/
version.ts`, both version-consistency unit tests, and
  `docs/canonical/canon-version.json`'s `repository_compatibility` upper
  bound widened to admit it). `CANON_VERSION` is unchanged (`0.3.0`) —
  this round implements the already-accepted canon 19a text; no further
  canon edit was made.
- `docs/handover/PACK-04-REPORT.md`.

### Verified

- **PACK-04 PASS**, confirmed by a complete external GitHub Actions run
  with real network access: 1599 Python tests passed, 2 skipped (genuine
  CT-00-11/12 not-applicable markers), TypeScript tests passed, frontend
  tests passed, a successful Next.js production build, and Ruff,
  Prettier, ESLint, and mypy all clean, with all 305 required paths
  present and no forbidden files. Full detail:
  `docs/handover/PACK-04-REPORT.md`.

## [0.3.0] - participation and decision kernel

### Added

- Six independent, in-memory-backed services (CLAUDE-PACK-03,
  "Participation and Decision Kernel"): `initiative-service`,
  `deliberation-service`, `moderation-service`, `voting-service`,
  `tally-service`, `delegation-service`, each with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interface, and in-memory
  reference adapter, following ADR-005's service decomposition.
- All 18 canon-scoped entities across the six new services: `Initiative`,
  `InitiativeVersion`, `SupportRecord`, `Amendment`, `SourceRecord`
  (initiative-service); `Discussion`, `Contribution`
  (deliberation-service); `ModerationCase`, `ModerationDecision`, `Appeal`
  (moderation-service); `Ballot`, `BallotOption`, `VoteEnvelope`,
  `VoteReceipt` (voting-service); `Tally`, `ResultPublication`
  (tally-service); `Delegation`, `DelegationSnapshot`
  (delegation-service) - each with its explicit `ALLOWED_TRANSITIONS`
  state machine (where canon defines a status enum), application-layer
  commands, canonical event construction, and `epd2_audit_core` audit
  entries for every state-changing action.
- `docs/adr/ADR-005` through `ADR-006`, `ADR-008` through `ADR-010`
  (service decomposition, reason-code additions, PACK-02 integration
  boundary, voting/delegation/quorum/tie/challenge/finality defaults, and
  the canon minor-version addition those defaults required), all accepted
  (ADR-009/ADR-010 with owner amendments) prior to this implementation.
- Structural, fail-closed enforcement of every accepted ADR-009 voting
  default: vote changes allowed until close with only the latest valid
  envelope counted (items 1-2); abstention modeled as an explicit
  `BallotOption` (item 3); `Ballot.ballot_method` restricted to
  `single_choice`/`yes_no` for this pilot (item 4); quorum optional per
  ballot (item 5); a second, distinct actor required to approve final
  ballot configuration (item 7, INV-08); `Delegation`/`DelegationSnapshot`
  implemented fully but disabled by default per ballot, maximum
  delegation depth 1 (items 8-9); a delegator's own direct vote overrides
  their delegate's (item 10); ties recorded as an explicit
  `tie_no_decision` outcome, never silently broken (item 11); and
  `Ballot.challenge_window_hours`/`ResultPublication.challenge_deadline_at`
  (canon 0.2.0, ADR-010) implemented with a 72-hour repository default,
  configurable per ballot, and a `compute_finality_state` function that
  can only ever return a provisional value - no PACK-03 code path may
  declare a `ResultPublication` final (items 12-13).
- ADR-009 item 14 (accepted with amendment): the canonical `invalidated`
  `Ballot` status and its transition structure are implemented, but no
  PACK-03 application-layer command can reach it - ballot invalidation
  authorization belongs entirely to the future Governance service.
- Structural identity-separation and vote-linkability guarantees
  (CT-00-08/CT-00-09) extended to `VoteEnvelope`, `VoteReceipt`, `Tally`,
  `ResultPublication`, `SupportRecord`, and `Delegation`: none may contain
  `account_id`, `person_id`, or `identity_record_id`, enforced via
  `additionalProperties: false` JSON Schemas and per-entity
  `FORBIDDEN_FIELD_NAMES` structural tests, plus a positive-space
  regression test proving no code path resolves a `VoteEnvelope` to an
  `Account`.
- The narrow, ADR-008-governed PACK-03 -> PACK-02 read boundary:
  `initiative-service` and `voting-service` call
  `epd2_credential_service.application.validate_participation_credential`
  and two new, additive, read-only `epd2_eligibility_service.application`
  query functions (`get_eligibility_decision`, `get_eligibility_snapshot`)
  - never either service's `storage`/`domain` modules. No other PACK-03
    service depends on PACK-02, no PACK-02 service depends on PACK-03, and
    no PACK-03 service imports another PACK-03 service's package.
- `contracts/reason-codes/pack-03.yml` (70 entries: 9 PACK-03-relevant
  canon section-24 codes, 5 reused generic canon codes, and PACK-03's own
  additive codes per ADR-006), 18 entity JSON Schemas and 18 event-payload
  JSON Schemas (`contracts/schemas/`, `contracts/events/`), and
  `contracts/openapi/pack-03.yaml` (71 paths, one per real application
  command, tagged per service).
- CT-00-01 through CT-00-10 extended to cover all six new services
  (`tests/contract/`); CT-00-11/12 remain explicitly not-applicable for
  PACK-03 (no `AIProcessingRecord`/`EmergencyAction` in scope), the same
  treatment PACK-02 gave them.
- `tests/repository/test_service_boundaries.py` extended with the PACK-03
  service matrix, the ADR-008 `.application`-only PACK-03->PACK-02 edges,
  and the one-way PACK-02/PACK-03 dependency direction, as their own
  dedicated, AST-based structural tests (not merely re-running the
  existing PACK-02-only check).
- `docs/handover/PACK-03-REPORT.md`.

### Changed

- `scripts/check_repository.py` `REQUIRED_PATHS` extended for every new
  PACK-03 path (six services, contracts, and the report).
- Root `pyproject.toml` / `package.json` workspace membership, `ruff`,
  `mypy`, and `pytest` configuration extended to cover the six new
  services; `Makefile`'s `typecheck` target gained six new scoped mypy
  invocations.
- `docs/canonical/canon-version.json`'s `repository_compatibility` range
  widened from `>=0.1.0 <0.3.0` to `>=0.1.0 <0.4.0` to admit
  `REPOSITORY_VERSION 0.3.0` - this is repository-side bookkeeping, not
  canon-immutable content; the canon document's own text and checksum are
  unchanged by this pack (still `0.2.0`,
  `5ed52c3a6a94e821323616ac369595fd364a71115cf5c1c6763d8edb51a6044a`).

### Verified

- **PACK-03 PASS**, confirmed by a complete external GitHub Actions run
  with real network access: 1525 Python tests passed, 2 skipped (genuine
  CT-00-11/12 not-applicable markers), TypeScript 3/3, frontend tests
  2/2, a successful Next.js production build, and Ruff, Prettier,
  ESLint, and mypy all clean, with all 277 required paths present and no
  forbidden files. Full detail: `docs/handover/PACK-03-REPORT.md`.

## [Unreleased] - canon minor version 0.2.0

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.1.0 →
0.2.0` (ADR-010, accepted with amendment) — the first edit to this
  document's own text since its original acceptance. Adds two
  backward-compatible fields: `Ballot.challenge_window_hours` (optional,
  repository default 72 hours, configurable per ballot) and
  `ResultPublication.challenge_deadline_at` (computed as `published_at +
challenge_window_hours`), plus a clarifying note that reaching
  `challenge_deadline_at` is necessary but not sufficient for finality —
  a canonical or explicitly approved technical-challenge registration and
  adjudication mechanism must exist first (its own future ADR).
  `docs/canonical/canon-version.json`, `packages/python/epd2-core/src/epd2_core/version.py`,
  and `packages/typescript/epd2-types/src/version.ts` updated to match;
  `REPOSITORY_VERSION` is unchanged (`0.2.0`) since no PACK-03 service
  code exists yet.

## [0.2.0] - identity separation and audit kernel

### Added

- Five independent, in-memory-backed services (CLAUDE-PACK-02):
  `account-service`, `identity-service`, `eligibility-service`,
  `credential-service`, `audit-core`, each with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interface, and in-memory
  reference adapter.
- `epd2-audit-core`: append-only, hash-chained `AuditEvent` store
  (canon 18.1, INV-04/INV-05) with idempotent append by `audit_event_id`
  and fail-closed conflict detection on a duplicate id with different
  content.
- Identity/participation separation (INV-01): `Account` -> `IdentityRecord`
  -> `EligibilityRule`/`EligibilityDecision`/`EligibilitySnapshot` ->
  `ParticipationCredential`, with no identity-linking field on the
  credential, enforced by an automated identity-leakage test suite.
- Centralized, executable reason-code registry
  (`contracts/reason-codes/pack-02.yml`), JSON Schemas
  (`contracts/schemas/`), event payload schemas (`contracts/events/`), and
  a transport-neutral OpenAPI contract (`contracts/openapi/pack-02.yaml`).
- Contract test suite (`tests/contract/`): CT-00-01 through CT-00-10,
  CT-00-11/12 explicitly marked not-applicable; identity-leakage,
  state-transition, audit, and Hypothesis property-based tests.
- ADR-002 (identity/participation separation and canonical event/name
  resolution), ADR-003 (append-only audit hash chain), ADR-004
  (centralized reason-code registry), plus new architecture docs
  (`docs/architecture/identity-participation-separation.md`,
  `docs/architecture/audit-kernel.md`) and
  `docs/review/PACK-02-THREAT-MODEL.md`.
- `docs/handover/PACK-02-REPORT.md`.

### Changed

- `scripts/check_repository.py` and `scripts/check_forbidden_files.py`
  updated for PACK-02 (new required paths; a filename-based check for a
  forbidden central identity-participation mapping table/file, pack
  section 15).
- Root `pyproject.toml` / `package.json` workspace membership, `mypy`,
  and `pytest` configuration extended to cover the five new services and
  `tests/contract/`.

## [0.1.0] - initial repository skeleton

### Added

- Repository skeleton for EPD² Civic OS (CLAUDE-PACK-01).
- Canonical domain and event model (TZ-00, canon version 0.1.0) placed at
  `docs/canonical/TZ-00-domain-event-canon.md`.
- Architecture documentation (`docs/architecture/`) and initial ADRs
  (`docs/adr/`).
- Root Python workspace managed with `uv`, and the `epd2-core` shared
  package (version constants, UUID identifier helpers).
- Shared TypeScript package `epd2-types` (version constants).
- Minimal Next.js frontend skeleton (`frontend/web-shell`).
- Repository structure checks and top-level tests
  (`scripts/`, `tests/repository/`).
- `Makefile` with a unified command interface (`setup`, `format`, `lint`,
  `typecheck`, `test`, `check-repository`, `verify`, `clean`).
- Pre-commit configuration and GitHub Actions CI workflow.
- Contribution, security, and CODEOWNERS documentation.
