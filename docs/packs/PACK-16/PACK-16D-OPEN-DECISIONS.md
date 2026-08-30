# PACK-16D — Open Decisions

**Round:** PACK-16D — Network-Enabled Finalization: Lockfile Regeneration,
Immutable ElectionGuard Provenance and Final Acceptance Alignment. A correction
of the PACK-16D reference-implementation candidate, not a new round.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

Every entry names what is undecided, who owns it, and what evidence would
close it. An entry with no closing condition is not an open decision — it
is an unowned risk, and none is recorded that way.

The first candidate recorded ten open decisions and closed none. The first
independent audit found that three of them were not decisions at all: they
were implementation work the round owed and had not done, filed under a
heading that made them look like somebody else's problem. Those three were
closed by implementation, and two genuinely new ones replaced them.

The **second** audit passed almost everything and named three narrower
faults, recorded here as `OD-P16D-13`, `-14` and `-15` so that what was
found has an identifier rather than living only in an audit transcript.
All three are now closed, and two entries — `OD-P16D-16` and `-17` — recorded
what the previous correction could not finish. Neither was a decision somebody
else owed: `-16` was one command on a networked machine, and `-17` a fetch that
sandbox blocked. They were open because they were _undone_, which is a different
and more uncomfortable category than _deferred_, and they were filed under their
real name.

**Both are now `CLOSED`** — the commands were run on a network-enabled host and
their outputs are recorded. That is the only thing this finalization closed.
Every other entry below is unchanged, and in particular `VO-08`, external
cryptographic review, a fully independent verifier, full ElectionGuard ecosystem
interoperability, constant-time production assurance, production HSM and key
custody, the production guardian ceremony and legal certification all remain
**OPEN**. A round that clears two environmental blockers has cleared two
environmental blockers; it has not become production-ready, and no entry here is
allowed to drift in that direction because a different one closed.

## 1. Decisions this correction closed

A decision is closed here only by an artefact that exists and a test that
fails if it stops existing. Nothing below is closed by assertion.

### `OD-P16D-01` — the `EPD2-CRYPTO-1` constants are not present — **CLOSED**

**What it said.** The profile was registered and unavailable;
`load_profile("EPD2-CRYPTO-1")` raised `ParameterProfileUnavailableError`
because the published 4096-bit `p` and the generator `g` could not be
obtained first-hand.

**What closed it.** The constants were obtained from a primary source —
`microsoft/electionguard-rust`, `src/eg/src/standard_parameters.rs`, which
states that it implements the ElectionGuard Design Specification v2.1.0
§3.1.1 page 14, "Standard Baseline Cryptographic Parameters" — and are
committed as
`reference/crypto/profiles/EPD2-CRYPTO-1.json` with
`parameter_digest = f0af5b71412ccf93a1eaf93364c223f5339cdb2815a2efcfa1bd775cd2bf17fb`
pinned in code.

**Why the transcription is trustworthy.** Not because the fetch succeeded.
The old entry was right that transcribing 1024 hex digits is where this
goes wrong, so the transcription is checked by mathematics that a single
wrong digit would break:

```
|p| = 4096                       |q| = 256
q = 2^256 - 189                  q | (p - 1)
p = q * r + 1                    1 < g < p,  g != 1,  g^q = 1 mod p
p probable prime                 q probable prime      r/2 probable prime
p's leading 256 bits all ones    p's trailing 256 bits all ones
p's middle 3584 bits agree with ln(2) for 3306 of 3584 bits
```

The `r/2`-prime property and the `ln(2)` derivation are the published
family's documented structure. The first candidate's same-size test profile
had **neither**, which is exactly why it was never a substitute and why the
audit was right to refuse it as one.

**Evidence.** `test_epd2_crypto_1.py` — 17 tests, 21.55 s, including
`test_epd2_crypto_1_structural_provenance` and
`test_epd2_crypto_1_invalid_constant_rejected`. The full cryptographic
suite runs on this profile.

**What did not close.** `VO-08`. Having the right constants and having an
assessment that these constants are appropriate for a binding German
election are different things, and only the first happened.

### `OD-P16D-07` — the guardian model implemented is single-guardian — **CLOSED**

**What it said.** `tally_accepted()` produced one share with
`guardian_index = 1`. Threshold DKG and both PACK-16B quorums were
unimplemented, deferred on the grounds that their correctness depended on
the parameter family `OD-P16D-01` left open.

**What closed it.** `reference/guardians/` — a Feldman verifiable
secret-sharing DKG with coefficient commitments and Schnorr proofs of
possession, share verification against published commitments, Shamir
threshold decryption in the exponent with Lagrange coefficients at zero,
and a generic `QuorumPolicy(k, n)`. The 3-of-5 default and the 4-of-7
high-assurance quorums both run, and `2k <= n` is rejected so two disjoint
sets can never each decrypt.

**Evidence.** `test_guardians.py` — 28 tests. 3-of-5 succeeds at `(1,2,3)`,
`(1,3,5)`, `(3,4,5)`, `(2,4,5)` and 2-of-5 is refused; 4-of-7 succeeds at
`(1,2,3,4)`, `(2,4,6,7)`, `(1,3,5,7)` and 3-of-7 is refused. A 3-of-5
ceremony also runs on `EPD2-CRYPTO-1`. `test_e2e.py::test_e2e_11` and
`::test_e2e_12` cover the threshold tally and the insufficient-quorum
refusal end to end.

**What did not close.** Key custody. The ceremony runs in one process. See
`OD-P16D-11`.

### `OD-P16D-09` — checkpoint signatures are carried but never verified — **CLOSED**

**What it said.** The board signed checkpoints with a symmetric HMAC key
that no third party holds, so `verify_board` carried the field and did not
check it. It was the eighth `NOT_CHECKED` entry and a declared production
blocker.

**What closed it.** `publication/checkpoint_signing.py`: Ed25519 (RFC 8032
PureEdDSA over edwards25519 with SHA-512) over a canonical payload binding
the schema version, profile, election, board, sequence, tree size, root,
previous-checkpoint hash, publication phase and key identifier, domain
separated under `BOARD_CHECKPOINT`. The trust anchor is a `SignerRegistry`
supplied **alongside** the export; no path reads a key out of the artefact
being verified, and `CheckpointPayload` has no `public_key` field at all.
Five distinct failure outcomes carry five distinct exit codes.

**Evidence.** `test_checkpoint_signatures.py` — 29 tests, including
`test_a_signer_registry_is_never_read_from_the_checkpoint` and
`test_verifier_reports_a_forged_signature_distinctly`. The RFC 8032 §7.1
published vectors pass, and every operation is cross-checked against
OpenSSL out-of-process.

**The production blocker is discharged.** `OD-P16D-05` remains the round's
only production blocker.

**What did not close.** Two things, and they are now their own entries:
who authorised the registry (`OD-P16D-12`), and whether the board showed
one view to everyone (`OD-P16D-06` — a valid signature is not evidence of a
single view, and a dedicated test constructs two _genuinely signed_
conflicting checkpoints to make the point).

### `OD-P16D-13` — the signature primitive was written here — **CLOSED**

**What the audit said.** `CHECKPOINT SIGNATURE PRIMITIVE POLICY: FAIL —
HANDWRITTEN ED25519`. `reference/crypto/ed25519.py` implemented
Edwards-curve point arithmetic, point compression and decompression, scalar
multiplication, private-key expansion, signing and verification.

**Why it was a real fault and not a technicality.** The previous round's
defence was that the algorithm was RFC 8032's, implemented as written, and
cross-checked against OpenSSL on 25 vectors. All of that was true and none
of it was the point. Agreement on the vectors an author thought to write is
not the property that matters for a curve implementation; what matters is
the vulnerability class the author did not think of — a missing subgroup
check, a branch that leaks a key bit, a non-canonical encoding accepted on
an input nobody tried. Those are found by years of adversarial attention on
one widely deployed implementation.

**What closed it.** `reference/crypto/signature_provider.py`: a
`CheckpointSignatureProvider` Protocol with six operations, one active
implementation over `cryptography` 46.0.7 (OpenSSL 3.5.6), strict raw
canonical encodings, fail-closed verification. `crypto/ed25519.py` is
**deleted**, not relocated. There is **no fallback**: the library is
imported at module scope and its absence raises
`SignatureProviderUnavailableError` at import time.

**Evidence.** `test_checkpoint_signatures.py` — 44 tests, including
`test_handwritten_ed25519_not_imported` (an `ast` walk over every module in
`reference/`), `test_missing_provider_fails_closed` (a subprocess with the
library blocked, preceded by a **control run** so the test cannot pass for
the wrong reason), and three RFC 8032 §7.1 published vectors.

**What did not close.** Constant-time assurance — see `OD-P16D-05`, which is
narrowed rather than closed. The dependency lock this entry opened as
`OD-P16D-16` was closed later, on a network-enabled host.

### `OD-P16D-14` — the parameter source reference was mutable — **CLOSED**

**What the audit said.** `PARAMETER SOURCE REPRODUCIBILITY: PARTIAL —
MUTABLE URL / DIGEST NOT IN ARTIFACT`. The artefact cited
`raw.githubusercontent.com/.../main/...`, and the only digest lived in an
evidence register rather than beside the values it vouched for.

**What closed it, and it is not what the finding literally asked for.** The
authoritative reference is now the **specification** at its versioned
release asset — `.../releases/download/v2.1/EG_Spec_2_1.pdf`, a tag, not a
branch — with its SHA-256 recorded **in the artefact**. The mutable URL
survives for a human reader with
`human_readable_url_is_authoritative: false`.

**And something better than either.** The artefact now carries a
`derivation` block, and the whole parameter set is reconstructed **offline,
from no source at all**: `p` from the published `ln 2` rule (3305 bits,
computed locally as `2·atanh(1/3)`) plus a recorded 279-bit offset, then
`q = 2²⁵⁶ − 189` in closed form, `r = (p−1)/q`, `g = 2^r mod p`. A URL tells
you where bytes came from. This tells you the bytes are the ones the
published rule produces, and a single wrong hex digit anywhere fails it.

**Evidence.** `test_epd2_crypto_1.py::test_epd2_crypto_1_parameters_reconstruct_offline`
and five further provenance tests, none of which touches the network.

**What did not close.** The commit pin on the corroborating Rust file, opened
here as `OD-P16D-17` and closed later, on a network-enabled host.

### `OD-P16D-15` — cross-checks ran mostly on the test profile — **CLOSED**

**What the audit said.** `CROSS-IMPLEMENTATION ON TARGET PROFILE: PARTIAL`.
The oracle existed and was useful; three of its nine operations ran on
`EPD2-CRYPTO-1` and the rest on the 1024-bit test group.

**What closed it.** `tests/reference/test_target_conformance.py` — 15 tests
covering all twelve core operations on `EPD2-CRYPTO-1` itself, from one
deterministic fixture set with fixed nonces, exported as
`PACK-16D-TARGET-PROFILE-FIXTURES.json`. The oracle gained a
`ballot_structural` handler that rebuilds the canonical bytes from the
ballot's **fields** before hashing, because handing it the producer's
canonical encoding would test the hash and not the encoding — and the
encoding is where the previous round's real defect was found.

Two invalid fixtures are refused by the oracle, both multiplied by `g` so
they stay **inside the subgroup** and fail on the mathematics rather than on
a cheap structural check a random value would also have failed.

**Evidence.** One documented command:
`pytest -m slow_conformance services/voting-service/tests/reference/`.
Timings are recorded per operation in
`PACK-16D-TARGET-PROFILE-TIMINGS.json` rather than used as an argument for a
smaller group.

**What did not close.** Comparison against a _complete_ independent
implementation — `OD-P16D-02`, unchanged.

## 2. Decisions this correction narrowed but did not close

### `OD-P16D-02` — no comparison against a complete independent implementation

**State, corrected.** The old entry said all evidence was self-generated.
That is no longer true, and the entry is narrowed rather than closed.

Conformance evidence is now classified in three tiers
(`reference/testing/conformance.py`), and the catalogue
`PACK-16D-CONFORMANCE-EVIDENCE.json` holds **13 entries: 2 primary-source
and 11 cross-implementation**, across two oracles that share no code with
the producer:

- **OpenSSL** via `cryptography` 46.0.7, run out-of-process under a
  different interpreter. 25 seed-message pairs agree byte for byte in both
  directions. If no such interpreter exists the test **fails loudly**
  rather than skipping.
- **A Node.js verifier** that re-derives the canonical encoding from the
  _written grammar_ and implements its own square-and-multiply modular
  exponentiation, importing only `node:` builtins. It cross-checks nine
  operations, three of them on `EPD2-CRYPTO-1` itself.

**What it found.** `encode_seq` was ambiguous: it concatenated items raw
after a count, so `SEQ([b"ab", b"c"])` and `SEQ([b"a", b"bc"])` produced
identical bytes. The oracle, written from the grammar rather than from the
code, disagreed — and that is how a real defect in a digest input surfaced.
Both encoders now length-prefix. Every digest in the round changed, and the
stability vectors duly caught that.

**What is still missing.** Two single-purpose oracles are not a complete
second implementation of ElectionGuard 2.1. Nothing here has been checked
against one.

**Owner.** PACK-17 independent verification.

**Closing evidence.** Vectors produced by a complete independent
ElectionGuard 2.1 implementation on the real parameter family, verified by
this one, and vice versa. **This is no longer dependent on `OD-P16D-01`**,
which is closed.

### `OD-P16D-06` — cross-mirror split-view detection is not implemented

**State.** `verify_board` detects rollback, equivocation and a broken chain
**within a single exported view**, re-derives every checkpoint root from the
exported entries, and now verifies the operator signature on each
checkpoint. It still cannot detect a board that shows two internally
consistent but different views to two different observers.

**Sharpened by this round.** Authenticity and consistency are now visibly
separate properties. A test constructs two checkpoints at one sequence with
different roots and **both signatures genuine**; `verify_board` returns
`BOARD_INCONSISTENCY`, and it can only do so because both views were
exported together. Across mirrors, nothing would.

**Why.** The standards landscape is unsettled, recorded in PACK-16C as
evidence `G-01`…`G-05`: RFC 9162 §11.3 places gossip out of scope, RFC 6962
§5 defers it, `draft-ietf-trans-gossip-05` expired in 2020, and C2SP
`tlog-witness` is not a ratified standard. Implementing an ad-hoc gossip
protocol would create a security claim nobody has reviewed.

**Owner.** PACK-17 resilience work.

**Closing evidence.** A witness or gossip mechanism chosen against a
published standard, with its threat model stated.

## 3. Decisions the previous correction opened — **both now CLOSED**

Both were environmental: work that had been attempted and that the build
environment prevented. Both named the exact command that would close them, and
both were held open by a test rather than by a paragraph. The commands were run
on a network-enabled host, and the entries are closed on their outputs.

### `OD-P16D-16` — the signature provider is declared but not locked — **CLOSED**

**Status: CLOSED. `DEPENDENCY LOCK: REGENERATED`.
`FROZEN CLEAN INSTALL: EXECUTED ON A NETWORK-ENABLED HOST`.**

**What it said.** `cryptography>=46.0.7,<47` was declared in
`services/voting-service/pyproject.toml` and absent from `uv.lock`, because
`uv lock` re-resolves the entire workspace and the build environment's egress
allowlist refused `pypi.org`. Hand-editing the lock was prohibited, and typing
plausible distribution hashes for wheels never downloaded would have produced a
file that looks resolved and is not.

**What closed it.**

```console
$ uv lock
$ rm -rf .venv
$ uv sync --all-groups --frozen
Checked 61 packages
```

```text
old uv.lock SHA-256   1a1e5a72b67b92a53b189e6eb9c9f4305f236a0aa76f7d55887f24ad2a76d543
new uv.lock SHA-256   b2d0775458d3b6e81d321724530c7a473584fb2b3d9d231d220d8e9dcdfe8066
resolved              cryptography 46.0.7, cffi 2.1.0, pycparser 3.0
lock delta            149 lines added, 0 removed, 0 existing versions changed
```

**How it was checked rather than taken on trust.** The lock is parsed as TOML,
not searched as text, because a string search matches the package name inside
another package's dependency list and reports an entry that does not exist. The
entry has a registry source, `sha256:`-prefixed hashes on all 43 artefacts, and
both transitives locked; `cryptography` appears in `epd2-voting-service`'s own
dependency list rather than as a stray root entry; the `requires-dist` specifier
echoes the manifest; and the imported library's version is asserted equal to the
locked one, which ties the code the suite exercises to the recorded resolution.

**What is still not claimed.** `uv sync --all-groups --frozen` ran on the
network-enabled host, not in the build session, which still has no package
index. "The tests are green" and "the frozen install passes" remain separate
claims and are recorded separately.

**Why it cannot silently re-open.**
`tests/repository/test_pack16d_signature_dependency.py` no longer tolerates the
blocked state: a missing lock entry now fails, an entry that looks typed rather
than resolved fails, and — the other direction —
`test_outstanding_lock_notice_did_not_outlive_the_lock` fails if the
`LOCK REGENERATION OUTSTANDING` notice is left behind after the lock caught up.
A to-do that outlives its cause is how a repository accumulates lies about
itself.

### `OD-P16D-17` — the corroborating upstream source is not commit-pinned — **CLOSED**

**Status: CLOSED. `IMMUTABLE UPSTREAM IMPLEMENTATION PROVENANCE: RECORDED` —
both halves pinned, and still recorded separately.**

**What it said.** `source.corroborating` carried `upstream_commit: null`,
`commit_pinned_source_url: null` and `source_sha256: null`, because four access
paths to GitHub were refused by two distinct mechanisms. No commit SHA and no
byte-exact digest could be obtained, and neither was invented.

**What closed it.**

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

`unpinned_reason` and `auditor_action` were removed in the same change that
added the pin, which `test_epd2_crypto_1_source_commit_present` enforces: a
repository that keeps an excuse beside the thing the excuse was for is telling a
reader two incompatible stories.

**What was not quietly restored.** The digest an earlier round computed over a
markdown rendering (`3afa2962…`) stays withdrawn, and the note recording the
withdrawal stays in the artefact. The digest now present is a different value
over different bytes, and the record says which is which.

**What the pin does and does not buy.** It buys **traceability**: a reader can
re-fetch the exact bytes the constants were first read from. It does not change
**correctness**, which never rested on this file — the values are established by
the normative specification and by the offline reconstruction in `derivation`,
neither of which consults it. And it does not promote the implementation source:
it remains `is_normative: false`, corroborating only.

**One limit, recorded in the artefact rather than here.** The digest was
computed on the network-enabled host. The build session verified the pin's
internal consistency and re-derived every parameter offline, but did not
re-fetch the upstream bytes, and `source_sha256_verification_scope` says so in
the artefact where a verifier will actually look. One command closes it:
`curl -sL <pinned-url> | sha256sum`.

### `OD-P16D-11` — the reference key ceremony has no custody model

**State.** `run_ceremony()` executes the entire distributed key generation
**inside one process**. Guardian polynomials, shares and the resulting
secret key shares are ordinary Python objects in one address space.

**What is therefore absent.** An authenticated channel between guardians —
a share is handed over by function call, not transmitted, so nothing
authenticates the sender or protects the share in transit. No hardware
security module. No air gap. No key custody, escrow policy or attestation.
No ceremony witnesses, no recorded procedure, no separation of duties.

**What is present, and why that is not the same thing.** The _protocol_ is
right: shares are verifiable against published commitments, a corrupt share
aborts the ceremony rather than silently degrading the key, no party ever
holds the joint secret, and no secret reaches the transcript — a test
searches the transcript's canonical bytes for every share and coefficient.
A correct protocol executed with no custody is a demonstration, not a
ceremony.

**Owner.** PACK-17, jointly with the production trustee architecture.

**Closing evidence.** A ceremony specification with named custody roles,
HSM-backed share generation, authenticated point-to-point channels between
guardian devices, and a rehearsed and witnessed procedure. Until then this
is a **production prerequisite** for any real election, distinct from the
production blocker `OD-P16D-05`: this one is missing procedure, that one is
a property the language cannot provide.

### `OD-P16D-12` — the signer registry's own authorisation is outside the verifier's reach

**State.** `verify_checkpoint` resolves a checkpoint's `signing_key_id`
inside the `SignerRegistry` it was handed and rejects anything it cannot
resolve. It cannot tell the reader that the registry it was handed is the
one the Election Board authorised.

**Why this is genuinely open rather than a bug.** The alternative — reading
the key out of the artefact under verification — is worse, and is
structurally prohibited here: anyone could then mint their own board. The
registry has to arrive out of band. Establishing _which_ out-of-band
registry is authentic is a governance and PKI question, not one a verifier
can answer from bytes.

**Consequence, stated where it is read.** This is the eighth `NOT_CHECKED`
entry, printed with every verification result including `VERIFIED`: the
verifier "checks a checkpoint against the signer registry it was given, and
cannot tell you that registry was authorised by the Election Board".

**Owner.** Governance, with PACK-17 for the distribution mechanism.

**Closing evidence.** A published, independently retrievable signer registry
bound to the election by a governance act, with a distribution and rotation
procedure a verifier operator can follow without trusting the board.

## 4. Decisions unchanged and still open

### `OD-P16D-03` — property tests are deterministic loops, not hypothesis strategies

**State.** `hypothesis` is a declared dev dependency but is not installable
here (PyPI returns HTTP 403). The 15 §41 properties run as seeded
deterministic loops of 40 cases each.

**What is lost.** Shrinking and adversarial search. These loops explore the
property space; they do not hunt for the input that breaks it, and they do
not minimise a counterexample when they find one.

**Owner.** PACK-17.

**Closing evidence.** The same 15 properties expressed as hypothesis
strategies, run with a non-trivial example budget, in an environment where
the dependency installs. `test_property_limitation_is_recorded` asserts
that `import hypothesis` still fails, so this entry cannot be quietly
closed by someone who forgot to convert the tests.

### `OD-P16D-04` — concurrency evidence covers one in-memory store

**State.** The nine §42 races run real OS threads against `ReferenceStore`,
whose transaction boundary is a re-entrant lock.

**What that proves.** The _logic_ is race-free under the serialisation this
store provides: no double acceptance, no double entitlement consumption, no
lost obligation, no orphan slot, no capability-to-ballot leakage.

**What it does not prove.** Anything about a production datastore. There
the same invariants must come from row-level locking or a serialisable
isolation level, and a lock that serialises everything is not a design a
real system can adopt.

**Owner.** PACK-17.

**Closing evidence.** The same nine races against the production data
plane, with the isolation level named and the locking strategy documented
per invariant.

### `OD-P16D-05` — constant-time and side-channel behaviour is not claimed

**State.** Python's arbitrary-precision integers and `pow()` are not
constant-time, and nothing here is written to be. This correction made the
statement **more precise rather than milder**, by separating four surfaces:

| Surface                                             | Secret-bearing? | Status                                                                                          |
| --------------------------------------------------- | --------------- | ----------------------------------------------------------------------------------------------- |
| public verification (proof, signature, Merkle)      | no              | timing carries no secret                                                                        |
| guardian secret operations (DKG, share computation) | **yes**         | pure Python; not constant-time                                                                  |
| secret nonce generation                             | **yes**         | OS CSPRNG; the _use_ is pure Python and not constant-time                                       |
| Ed25519 private-key signing                         | **yes**         | now OpenSSL, which pursues side-channel resistance as a design goal — **narrowed, not assured** |

The first correction **widened** this entry: threshold guardian operations
and Ed25519 signing were new secret-bearing surfaces. The final correction
**narrowed one of the four**: signing moved from a hand-written
non-constant-time implementation to OpenSSL. That is a real reduction in
risk and it is **not an assurance** — EPD² has measured nothing, and a
library's stated design goals are not this repository's evidence. The other
three surfaces are unchanged and remain pure Python, which is why the entry
stays open and stays a production blocker.

**Why it was not fixed.** It cannot be, in this language, at this layer.
Making it true requires a constant-time bignum implementation, which means
either a vetted native library — which the dependency policy would have to
be opened for, deliberately and with review — or a different language for
the cryptographic core.

**Owner.** PACK-17, jointly with the external cryptographic review.

**Closing evidence.** A constant-time implementation with measured
timing-variance evidence from an independent party. Absent that, this is
the round's **production blocker**, not a residual nicety.

### `OD-P16D-08` — no production authentication

**State.** `ReferenceApi` performs no authentication. The
`capability_reference` it takes is a test-only anonymous capability
fixture: a string naming a row in the reference store. The class docstring
and `API_BANNER` both say `NOT PRODUCTION AUTHENTICATION`.

**Owner.** Integration with the PACK-14 and PACK-15 credential boundary.

**Closing evidence.** A capability that arrives through that boundary, is
verified rather than looked up, and is never a bare string a caller can
supply.

### `OD-P16D-10` — the reference tally handles one ballot style

**State.** `tally_accepted()` iterates `manifest.ballot_styles[0]` only. An
election with more than one ballot style is not tallied correctly by the
reference builder. Fixtures A, B and C each declare a single style, so no
test exercises the gap — which is why it is recorded here rather than
discovered later.

**Owner.** A later PACK-16 implementation round.

**Closing evidence.** A multi-style fixture, a tally that iterates every
style, and reconciliation that accounts for options appearing in more than
one style.

## 5. Decisions inherited and still open

These are not PACK-16D's to close and are listed so that no reader mistakes
this round's silence for resolution.

| ID           | Decision                                             | Owner                                                                      | PACK-16D's effect                                                                                                                                                                            |
| ------------ | ---------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VO-08`      | BSI conformity of the cryptographic parameter family | PACK-16B external cryptographic review, independently confirmed in PACK-17 | **OPEN.** The parameters are now present and arithmetically checked, which is a precondition for the assessment and not the assessment. Named in `NOT_CHECKED`; no BSI conformity is claimed |
| `OD-P16A-07` | Encrypted-ballot retention period                    | PACK-09 / PACK-17                                                          | Untouched                                                                                                                                                                                    |
| `OD-P16C-04` | Serialization of board entries                       | Governance                                                                 | This round proposes `EPD2-ENC-1` as an implementation, **corrected this pass** so that sequences and structs length-prefix their members; the decision itself remains with governance        |
| `OD-P16C-09` | Verification-report governance                       | Governance                                                                 | Untouched                                                                                                                                                                                    |
| `OD-P16C-10` | Batch interval, capacity and checkpoint interval     | Governance                                                                 | The implementation takes them as declared inputs and validates them; it does not choose them                                                                                                 |
| `OD-P16C-14` | Commitment construction                              | Review                                                                     | This round implements one; review owns confirming it                                                                                                                                         |
| `OD-P16C-16` | Opening and reconciliation format                    | Review                                                                     | This round implements one; review owns confirming it                                                                                                                                         |

## 6. Rules that govern this list

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `OD-01` | **Across three corrections, eight entries closed and four opened.** The first closed `OD-P16D-01`, `-07`, `-09` and opened `-11`, `-12`. The second closed `-13`, `-14`, `-15` and opened `-16`, `-17`. This finalization closed `-16` and `-17` and opened nothing. **Nine entries remain open**, and no inherited decision was closed by any of the three                                                                                                                                                                                |
| `OD-02` | **An entry is closed by evidence, not by a later round asserting it.** Each open entry names the evidence that would do it, and each closed entry names the artefact and the test that did                                                                                                                                                                                                                                                                                                                                                 |
| `OD-03` | **`OD-P16D-05` is the round's production blocker**, narrowed to three surfaces rather than four. `OD-P16D-09`'s blocker status was discharged earlier. `OD-P16D-11` is a production _prerequisite_: procedure that does not exist, rather than a property the language cannot supply                                                                                                                                                                                                                                                       |
| `OD-06` | **`OD-P16D-16` and `-17` were a third category, and naming it is what made them closable.** They were not deferred and not blocked by another party — they were work that had been attempted and that the environment prevented. Because each named the exact command that would close it, closing them required running those commands and recording the output, not re-deciding anything. Both are now `CLOSED`                                                                                                                          |
| `OD-07` | **The blocked state was re-probed each round rather than carried forward, and that is what proved it environmental.** A blocker asserted once and then quoted from memory is indistinguishable from an excuse. Every command and every error string stayed reproduced verbatim in `PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md` so that a reviewer with network access could run the same commands and see a different result. That is exactly what then happened, and the resolving outputs sit beside the failing ones in the same document |
| `OD-08` | **Neither was ever closed early, downgraded in importance, or absorbed into another entry.** While they were open the acceptance matrix was corrected _downward_ to match them (`AM-79`), rather than the entries being softened to match the matrix. They are closed now on recorded command output, and `AM-79` and `AM-89` were promoted against the five stated conditions rather than on the blockers' disappearance                                                                                                                  |
| `OD-04` | **`OD-P16D-02` no longer depends on `OD-P16D-01`.** The parameter family is present, so interoperability work is unblocked and is simply not done                                                                                                                                                                                                                                                                                                                                                                                          |
| `OD-05` | **A closed entry stays closed only while its test does.** Every closure above names a test that fails if the artefact is removed or weakened; none is closed by narrative                                                                                                                                                                                                                                                                                                                                                                  |

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
