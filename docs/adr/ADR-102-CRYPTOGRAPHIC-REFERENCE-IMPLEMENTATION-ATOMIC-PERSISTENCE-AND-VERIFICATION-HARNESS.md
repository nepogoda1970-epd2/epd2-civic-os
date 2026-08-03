# ADR-102 — The specified voting model is built once, in reference form, so that its claims can be run rather than read

**Status:** proposed
**Round:** PACK-16D — Network-Enabled Finalization: Lockfile Regeneration,
Immutable ElectionGuard Provenance and Final Acceptance Alignment.
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`

**REFERENCE IMPLEMENTATION. NOT PRODUCTION CODE. NOT CERTIFIED. NOT A PASS.
NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION
PROHIBITED BY DEFAULT.**

Evidence references `[G-nn]` resolve in
`docs/packs/PACK-16/PACK-16C-PROTOCOL-EVIDENCE-MATRIX.md`.

---

## Context

Three rounds specified a voting model. PACK-16A chose the protocol family
and the ballot model, PACK-16B fixed the cryptographic parameters, the
guardian quorum and the key ceremony, PACK-16C fixed casting, the receipt,
the bulletin board and the election record. None of them ran.

A specification that has never been executed contains a particular kind of
error that review does not reliably catch: the claim that is coherent on
the page and impossible in the machine. An atomic boundary that reads
correctly can still have a check outside its transaction. A capacity plan
that partitions cleanly in prose can still leave unclassified slots when
the arithmetic is written down. A Merkle tree described as "standard" can
still be built in the shape where two different leaf sequences share a
root.

PACK-16D exists to find those errors while they are still cheap. Its
purpose is not to produce deployable software; it is to make the specified
model executable, and then to attack it.

**What the correction changed, and why this ADR was rewritten rather than
appended to.** An independent audit of the first candidate passed the
harness and failed four things: the actual `EPD2-CRYPTO-1` profile, the
threshold guardian model, checkpoint authenticity, and external
conformance. Each was a case of this ADR describing a *gap* in language that
made it sound like a *decision*. "The constants could not be obtained" is a
report; "a profile that fails closed is a visible gap" is a rationalisation
of it. The four are now implemented, and the sections that argued for their
absence are replaced rather than annotated — an architecture decision record
that carries both the old argument and its refutation teaches a reader
nothing about what the system is.

One further consequence deserves the top of the document. The independent
Node.js oracle written to satisfy the conformance finding was written from
the *documented grammar* rather than from the code, and it disagreed with
the code: `encode_seq` concatenated its items raw after a count, so
`SEQ([b"ab", b"c"])` and `SEQ([b"a", b"bc"])` produced identical bytes. Two
different sequences shared a digest, in a function every protocol digest
runs through. No self-generated vector could ever have found it. That single
defect is the strongest argument in this round for the audit's judgement,
and it is the reason external conformance is now a section of this ADR
rather than a deferred item.

**A second audit, and the three things it changed.** A further independent
audit of the corrected candidate passed the harness, the real
`EPD2-CRYPTO-1` profile, the 3-of-5 and 4-of-7 threshold paths and the
checkpoint signature semantics, and returned three findings:
`CHECKPOINT SIGNATURE PRIMITIVE POLICY: FAIL — HANDWRITTEN ED25519`,
`PARAMETER SOURCE REPRODUCIBILITY: PARTIAL — MUTABLE URL / DIGEST NOT IN
ARTIFACT`, and `CROSS-IMPLEMENTATION ON TARGET PROFILE: PARTIAL`. All three
were correct. **Only three things changed in response**, and everything else
was preserved unmodified: the guardian model, the atomic transactions, the
sealed batches, the checkpoint payload semantics, the signer trust model,
the Merkle mechanics, the election record, the verifier boundary, the
negative corpus, and the concurrency and fault-injection harnesses.

The first of the three cost this ADR an argument it had made at length and
made wrongly. *Dependency decision* below is **replaced**, not appended to,
for the same reason the earlier sections were: an ADR that carries both a
claim and its refutation teaches a reader nothing about what the system is
or why.

## Inherited ADRs

`ADR-099` (protocol and ballot model), `ADR-100` (parameters, ceremony,
trustees) and `ADR-101` (casting, receipt, board, record) are **all
`proposed`**. This ADR does not accept, ratify or upgrade any of them, and
building against a proposed decision does not settle it. If review changes
one, this implementation changes with it.

## Implementation objective

Build the smallest thing that makes every PACK-16A/16B/16C claim testable,
and test it adversarially. Specifically: reference cryptography on the
**real** parameter profile, canonical encodings, the two atomic
transactions, threshold guardians, sealed batches, an authenticated bulletin
board, the election record and an independent verifier — plus a harness of
test vectors, external conformance evidence, a negative corpus, property
tests, concurrency races and fault injection.

Explicitly **not** an objective: production readiness, performance,
operational tooling, or breadth. Where a choice existed between covering
more surface and making a smaller surface provable, the smaller surface
won.

**"Smallest" is not a licence to omit a specified mechanism.** The first
candidate treated the parameter profile, the guardian quorum and checkpoint
authenticity as surface it could defer, and each deferral was written up as
a considered trade-off. They were not trade-offs: without them the reference
implementation was not exercising the model PACK-16A/16B/16C specified. The
boundary that matters is between *making the specified model executable* and
*making it deployable*, and only the second is out of scope.

## Language decision

**Python ≥3.12**, matching the repository's 22 workspace members. The
alternative — a separate cryptographic core in a systems language — was
rejected for this round because it would have made the reference
implementation harder to read than the specification it implements, which
defeats the purpose. That decision has a real cost, recorded under
*Constant-time limitations*, and it is not the right decision for
production.

## Dependency decision

**One cryptographic dependency, for the one primitive the standard library
does not supply.** `cryptography>=46.0.7,<47` is declared in
`services/voting-service/pyproject.toml` and is used for Ed25519 and for
nothing else — no X.509, no TLS, no symmetric primitives, no KDF. The
protocol's hash, HMAC, CSPRNG and modular exponentiation remain `hashlib`,
`hmac`, `secrets` and Python's arbitrary-precision integers, which supply
them honestly because they are compositions of primitives the standard
library exposes. It does **not** expose an asymmetric signature scheme.

**The argument this section used to make was that zero dependencies is the
strongest possible form of dependency compliance. That argument was wrong,
and an audit proved it.** It is replaced here rather than qualified,
because it was not a trade-off that turned out badly — it was a category
error, and leaving it on the page next to its refutation would invite the
next reader to make it again.

The error was to treat "no exposure was created" as equivalent to "the
exposure was assessed and is acceptable". Those are different claims about
different risks. Not adding a library removes supply-chain exposure. It does
not remove cryptographic-implementation exposure; it *relocates* it, from a
library with years of adversarial attention on it into a file in this
repository with none. The previous round then wrote Edwards-curve point
arithmetic, point compression, scalar multiplication and private-key
expansion by hand, checked it against RFC 8032's published vectors and
against OpenSSL, found agreement, and presented that agreement as
assurance.

**Agreement on the vectors an author thought to write is not the property
that matters for a low-level primitive.** What matters is the vulnerability
class the author did not think of: a missing subgroup check, a branch that
leaks a key bit, a non-canonical encoding accepted on some input nobody
tried. Those are found by years of adversarial attention paid to one widely
deployed implementation, and they cannot be found by the author of a fresh
one — not by more vectors, and not by a more careful author. The audit's
finding was `CHECKPOINT SIGNATURE PRIMITIVE POLICY: FAIL — HANDWRITTEN
ED25519`, and it was right on exactly this ground.

So the arithmetic is gone. `crypto/ed25519.py` is **deleted**, not
deprecated and not relocated: a file kept "for reference" is still
from-scratch curve code in the repository, one import away from being active
again. `crypto/signature_provider.py` replaces it as a **port, not an
implementation** — a `CheckpointSignatureProvider` Protocol with six
operations, and one active implementation over `cryptography`, which is
OpenSSL underneath. Six library calls, all in that one module, asserted by
an `ast` test that also fails if any other module under `reference/` imports
`cryptography`.

**There is no fallback, and the absence is the point.** The library is
imported at module scope; if it is missing, `SignatureProviderUnavailableError`
is raised and the process does not start. A
`try: import cryptography / except: use our own curve code` would silently
reinstate exactly what the audit removed, on whichever machine happened to
lack the dependency — and that machine is the one you would least want
running hand-rolled cryptography.

**What the dependency actually costs, assessed rather than asserted.** The
four prohibited shapes are re-run properly in
`PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md` §3, and none is present:
`cryptography` is a released version range from the public index, not a Git
branch; it is resolved at install time, not downloaded at runtime; it is
server-side Python, not a browser CDN script; and it is open source under
Apache-2.0 / BSD-3-Clause. The real costs are two, and both are recorded:
it links a **compiled Rust binding layer over OpenSSL's libcrypto**, so a
platform-specific native artefact is now in the runtime path and a libcrypto
CVE is an EPD² concern; and the provider is declared **and locked**.

**`DEPENDENCY LOCK: REGENERATED`; `FROZEN CLEAN INSTALL: EXECUTED ON A
NETWORK-ENABLED HOST`.** For two rounds this paragraph recorded the opposite,
because `uv lock` must re-resolve the entire workspace against an index the
build environment refused with HTTP 403, `uv lock --offline` failed on
`hypothesis`, and hand-editing a lock is prohibited — a `[[package]]` block
needs a registry source and distribution hashes for artefacts that were never
downloaded, and typing plausible hashes produces a file that looks resolved and
is not. The commands were run on a host with access:

```console
$ uv lock
$ rm -rf .venv && uv sync --all-groups --frozen
Checked 61 packages
```

`uv.lock` goes from `1a1e5a72…d543` to `b2d07754…8066`; `cryptography 46.0.7`
resolves from `https://pypi.org/simple` inside the `epd2-voting-service` graph,
with `sha256:` hashes on all 43 artefacts and the `cffi 2.1.0` / `pycparser 3.0`
chain locked beside it; 149 lines added, none removed, no existing version
changed. The build session that produced the candidate verified the lock's
parsed contents and asserted the imported library's version equal to the locked
one, but still has no package index and did not re-run the install — so **this
round claims a regenerated, hash-pinned lock, and records the frozen install as
performed on the network-enabled host rather than here.**

`package-lock.json` is unchanged: the Node.js oracle imports only `node:`
builtins and no npm package is involved. The test oracles are deliberately
**not** dependencies — cross-implementation evidence is worth something only
when the comparing implementation shares no code with the compared one, and
vendoring an oracle would destroy the property it exists to establish.

**One dependency is a ceiling this round claims, not a direction of
travel.** The provider covers signatures. It is deliberately not used for
hashing, randomness or the group arithmetic, because widening its footprint
would trade a reviewable implementation for an unreviewed one with no audit
finding asking for it. A future round that adds a second cryptographic
dependency — most plausibly for the constant-time bignum path — re-opens all
four assessments.

## Cryptographic module boundaries

`crypto/` depends on nothing else in the package. `casting/` depends on
`crypto/`. `publication/` and `election_record/` depend on both.
`verification/` depends on the public artefact types and on **no private
state** — a boundary enforced by a test that parses the verifier's imports
with `ast`, not by convention. `testing/` depends on everything and nothing
depends on it.

`guardians/` depends on `crypto/` only. `publication/checkpoint_signing.py`
depends on `crypto/` and on nothing in `casting/`, so a signature can be
verified by a party holding no ballot state at all.

Every domain-separated protocol digest goes through one function,
`crypto/hashing.h()`, and every label through one registry. Three hash
sites deliberately bypass the registry because none computes a protocol
digest: the idempotency request digest, counter-mode block generation in
the deterministic test source, and the board fixture's derivation of a
32-byte Ed25519 seed from a short human-readable test key. The checkpoint
*signing input* is not among them — it goes through `h()` under the
`BOARD_CHECKPOINT` label, so a signature over some other EPD2 structure can
never be presented as a checkpoint signature.

## Parameter profile

**`EPD2-CRYPTO-1` carries the real ElectionGuard 2.1 standard baseline
parameters and the whole stack runs on them.** The constants live in
`crypto/profiles/EPD2-CRYPTO-1.json` as canonical lower-case fixed-width
hex.

**The provenance was restructured by this correction, because the audit
found it resting on a branch.** `PARAMETER SOURCE REPRODUCIBILITY: PARTIAL —
MUTABLE URL / DIGEST NOT IN ARTIFACT` was a correct finding: a
`raw.githubusercontent.com/.../main/...` reference is a moving target, and
a parameter set is the last thing that should point at one. The artefact
now distinguishes three things that were previously one.

**Authoritative — the specification, not an implementation of it.**
`source.authoritative` names the *ElectionGuard Design Specification*
**2.1.0**, §3.1.1 page 14, at
`https://github.com/microsoft/electionguard/releases/download/v2.1/EG_Spec_2_1.pdf`
— a **versioned release asset under the tag `v2.1`**, which is the property
that matters: it is not a branch and it does not change under a reader. Its
SHA-256 `a263ab3c…b936` is recorded **inherited from PACK-16B evidence
`F-01`, where it was taken first-hand, and NOT re-verified this round** —
the document could not be retrieved in this environment, and
`document_sha256_provenance` says exactly that in the artefact.

**Corroborating — the Rust file, demoted and honestly labelled.**
`source.corroborating` keeps `microsoft/electionguard-rust`,
`src/eg/src/standard_parameters.rs` as the place a reader can most easily
look at the constants, with `human_readable_url_is_authoritative: false`.
It now carries a commit pin — `520651138110a13f777409e96606454df928ceac`
(2025-02-02), `commit_pinned_source_url` containing that commit and that path,
and `source_sha256 = ad38bfa68d31131a7d721e08d359224b21e967aae4d517534a60a109e10f5770`
over the file's raw bytes, retrieved 2026-08-03. For two rounds all three were
explicit `null`s, because four access paths were refused by **two distinct
mechanisms** — `api.github.com` by a per-repository access broker, and
`raw.githubusercontent.com`, `git clone` and the CDN mirrors by the egress
allowlist — and inventing a hash was never an option. **The earlier
`3afa2962…` digest stays withdrawn, not relabelled**: it was computed over a
markdown rendering rather than over the raw bytes, and a digest that names the
wrong byte stream is worse than none, because it invites exactly the check it
cannot survive. `unpinned_reason` and `auditor_action` were removed in the same
change that added the pin, which a test enforces, and
`source_sha256_verification_scope` records that the digest was computed on the
network-enabled host rather than re-fetched here. That closes `OD-P16D-17`.

**Pinning it does not promote it.** The implementation source stays
`is_normative: false`; the specification remains the authoritative reference and
the values remain established by the offline derivation below.

**Derived — and this is the part that does not need a network at all.** The
artefact's new `derivation` block rebuilds the entire parameter set from the
published structural rule:

```
p          = ONES(256) || M(3584) || ONES(256)
M          = (first 3305 fractional bits of ln 2) << 279 | delta_low
delta_low  = 0x445744fb5f2da4b751005892d356890defe9cad9b9d4b713e06162a2d8fdd0df2fd608   (279 bits)
q          = 2**256 - 189
r          = (p - 1) // q
g          = pow(2, r, p)
```

`ln 2` is computed locally as `2*atanh(1/3)` — not tabulated, not fetched.
All four constants reconstruct exactly. **A URL says where bytes came from;
a derivation says the bytes are the ones the published rule produces**, and
that is a stronger claim than any retrieval record, because a transcription
error anywhere in `p`, `q`, `g` or `r` fails reconstruction. It is why the
missing commit pin weakens the provenance trail without weakening the
values. It is also an **inference by this round** and not a statement by the
specification's authors, and it is recorded as one.

**The arithmetic checks stay, because reconstruction and verification catch
different things.** Every property the published family is documented to
have is verified locally, and a single wrong digit breaks all of them:

```
|p| = 4096                       |q| = 256
q = 2^256 - 189                  q | (p - 1)
p = q * r + 1                    1 < g < p,  g != 1,  g^q = 1 mod p
p probable prime                 q probable prime      r/2 probable prime
p's leading 256 bits all ones    p's trailing 256 bits all ones
p's middle 3584 bits agree with ln(2) for 3306 of 3584 bits
p reconstructs from the ln 2 rule and delta_low
g = 2^r mod p                    r = (p - 1) / q
```

`parameter_digest = f0af5b71412ccf93a1eaf93364c223f5339cdb2815a2efcfa1bd775cd2bf17fb`
is unchanged by the restructuring and is pinned in code as
`EPD2_CRYPTO_1_PARAMETER_DIGEST`, so editing the artefact is detected rather
than absorbed. The artefact's `digests` block now separates it from a
`source_sha256` — one is over the local canonical parameter tuple, the other
would be over an upstream file's exact bytes — each with its own written
definition, so the two can no longer be read as the same kind of claim.

**None of this narrows `VO-08`.** The artefact carries
`specification_review_status: "VO-08 OPEN — no BSI assessment of this family
exists"` so the gap travels with the parameters rather than being left in a
document.

**There is no fallback, by construction.** `load_profile` contains no
`except`, no default and no reference to any test profile — a structural
test parses the function's source to prove it. `require_target_profile()`
raises `ProfileSubstitutionError` with reason code
`PARAMETER_SET_NOT_APPROVED` for anything that is not the target. Four
environment variables and a feature flag were tried in a test; none
redirects the loader. A silent downgrade to a smaller group is the failure
mode that would make every result meaningless while every test stayed
green, so it is closed off in code rather than discouraged in prose.

The two fast profiles are renamed to say what they are —
`EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256` and
`EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160` — each file opening with `# TEST
ONLY / # NOT EPD2-CRYPTO-1 / # NOT ELECTIONGUARD 2.1 CONFORMANCE / # NOT
PRODUCTION`. A test asserts every non-target profile id contains the marker
`TESTONLY-NOTCONFORMANT`. The old names invited exactly the substitution
this section forbids: `EPD2-TEST-P4096-Q256` has `EPD2-CRYPTO-1`'s *shape*
and neither its `r/2`-prime property nor its `ln(2)` derivation, and a name
that differs only by the word `TEST` is not a safeguard.

Expected bit lengths live in `PROFILE_BIT_LENGTHS` **in code**, not in the
`.params` files, so the length check cannot compare a value against itself.
An earlier version did exactly that, in two places.

**Cost, recorded rather than optimised away.** On `EPD2-CRYPTO-1` a
selection encryption takes 0.043 s, a selection proof 0.086 s, a whole
ballot encryption 0.562 s, an accumulation 0.112 s, a 3-of-5 ceremony
2.074 s and the threshold shares 0.213 s; `test_epd2_crypto_1` is 25 tests
in 28.12 s and `test_target_conformance` 15 tests in 8.06 s. Those numbers
are written to
`tests/reference/vectors/PACK-16D-TARGET-PROFILE-TIMINGS.json` next to the
fixtures, regenerated on each run, so the cost is a published figure rather
than an argument. No validation was disabled and no reduced group
substituted to make any of it smaller. A reference implementation that is
slow on the real parameters is telling the truth about the parameters.

## Canonical encoding

`EPD2-ENC-1`: a canonical **binary tuple** encoding, not canonical JSON.
Fixed-width unsigned integers with no short form, length-prefixed byte
strings, NFC-normalised text, ordered structures that are **never sorted**,
duplicate field names rejected, and maps prohibited outright because a map
has no order. Group elements are always `|p|` bytes and scalars always
`|q|` bytes, so there is no short form for two implementations to disagree
about.

JSON was rejected because canonical JSON is a specification of how to avoid
a format's ambiguities. Choosing a format without them is simpler to verify
than choosing a discipline for using an ambiguous one.

**Sequences and structures length-prefix every member.**
`SEQ = UINT(len, 4) || BYTES(item)…`, and `STRUCT` encodes each field value
as `BYTES` rather than appending it raw. This is what the grammar always
said; it is not what the code did until the independent oracle disagreed
with it. Concatenating members raw makes the encoding ambiguous —
`SEQ([b"ab", b"c"])` and `SEQ([b"a", b"bc"])` flatten to the same bytes —
which means two different structures could share a protocol digest. Both
encoders were fixed, every digest in the round changed as a result, and the
stability vectors duly caught the change. The lesson is recorded in the
function's own docstring, where the next person to "simplify" it will read
it.

## Domain separation

`EPD2-DS-1`: 27 labels in one registry; `require_label()` fails closed on
anything unregistered. Digests are never truncated. There is deliberately
no unkeyed convenience wrapper, because a convenience wrapper is how a
domain-separated hash becomes an undomain-separated one.

Nine labels have no call site this round — two fewer than in the first
candidate, because `GUARDIAN_COMMITMENT` and `GUARDIAN_PROOF` acquired real
call sites when the threshold ceremony arrived. Rather than leave a registry
making a claim it does not back, `RESERVED_WITHOUT_CALL_SITE` names them and
a test asserts the set is exactly accurate. `BATCH_COVER_LEAF` is unused **by
design**: a cover leaf is uniform random bytes and is never hashed.

## Randomness

Production randomness is the OS CSPRNG with no seed, no reseed hook and no
fallback; a failure raises rather than degrades, on both `random_bytes` and
`random_below`. The deterministic test source requires **two** independent
guards — an explicit keyword *and* an environment marker — so that neither a
stray argument nor a stray environment variable is sufficient.
`select_source()` accepts only the literal string `"production"` and has no
code path that returns a deterministic source. That last property is
asserted by test rather than by reading the function.

## Proof implementation

Disjunctive Chaum–Pedersen per selection, Chaum–Pedersen for the contest
sum, Chaum–Pedersen for each decryption share; Fiat–Shamir over
domain-separated transcripts bound to the base hash, the ballot, the contest
and the option, so a proof does not transfer between selections or ballots.
Decryption-share proofs are bound to the contest and option they decrypt
through an exported context function that the verifier derives
independently — an earlier version used a bare literal and bound nothing.

Every verifier checks subgroup membership of every proof element, and of the
public key it is handed, and the range of every scalar, **before** evaluating
any equation.

## Threshold guardians

**Feldman verifiable secret sharing, with a generic quorum engine.**
Guardian `i` draws a polynomial `P_i` of degree `k−1` over `Z_q`, publishes
coefficient commitments `K_{i,j} = g^{a_{i,j}}` and a Schnorr proof of
possession of `a_{i,0}`. Guardian `l` receives `P_i(l)` and checks
`g^{P_i(l)} = Π_j K_{i,j}^{l^j}`, so a wrong share is **detectable rather
than absorbed** — `run_ceremony(corrupt_share_from=…)` exists to demonstrate
the abort path, not to work around it. The secret share is
`s_l = Σ_i P_i(l) mod q` and the joint key `K = Π_i K_{i,0}`; **no party
ever holds the joint secret**, and a test searches the transcript's
canonical bytes for every share and coefficient to prove none leaks.

Decryption is Shamir in the exponent: `M_l = α^{s_l}` with a Chaum–Pedersen
proof, Lagrange coefficients evaluated at zero, `g^m = β / Π M_l^{w_l}`,
bounded decode. `guardian_public_share_key()` derives `g^{s_l}` from public
commitments alone, which is how a verifier checks a share it may not see.

**The quorum is a property of the ceremony, not an argument to the caller.**
`combine_shares` reads `k` from the transcript; a transcript with a
rewritten quorum fails `verify_ceremony`, because the joint key no longer
derives from the roster. `QuorumPolicy(k, n).validate()` additionally
rejects `2k ≤ n`, since two disjoint sets that could each decrypt is not a
threshold. The PACK-16B configurations are unchanged: 3-of-5 default,
4-of-7 high assurance, with the engine generic in `k` and `n`.

**Compensated decryption is prohibited and the prohibition is
discoverable.** `compensated_decryption_share()` exists solely to raise
`CompensatedDecryptionProhibited`. A function that is absent teaches a
future implementer nothing; a function that refuses, with a reason, teaches
them why. A test greps the module for `compensate`, `reconstruct_secret`,
`escrow` and `break_glass`.

What this is **not** is a key ceremony. Everything above happens in one
process, with shares handed over by function call: no authenticated
channel, no HSM, no air gap, no custody, no witnesses. That is `OD-P16D-11`,
and it is a production prerequisite rather than a rough edge.

## Checkpoint authenticity

**Ed25519, RFC 8032 PureEdDSA over edwards25519 with SHA-512, supplied by a
vetted provider.** The first candidate signed checkpoints with a symmetric
HMAC key that no third party holds, and the verifier consequently did not
check the result. A signature nobody can verify is decoration, and the audit
was right to call it that.

The second candidate fixed that with a hand-written Ed25519, and the second
audit was right to fail *that*. **The primitive is now
`crypto/signature_provider.py`**, a narrow port over `cryptography` 46.0.7,
linked against OpenSSL 3.5.6. `CheckpointSignatureProvider` is a
`@runtime_checkable` Protocol with six operations — `generate_test_keypair`,
`load_public_key`, `sign_checkpoint`, `verify_checkpoint`,
`public_key_bytes`, `signature_bytes` — and `CryptographyEd25519Provider` is
the single active implementation, exposed as one module-level `PROVIDER`
with no selection mechanism, because a provider chosen by configuration is a
provider an operator can get wrong. `crypto/ed25519.py` is deleted. The
reasoning is in *Dependency decision*; the consequences are here.

**Encodings are strict and singular.** A public key is exactly 32 raw bytes
and a signature exactly 64: no PEM, no DER, no base64. Accepting several
encodings would mean two byte strings naming one key, and a signer registry
keyed on bytes would then hold two entries for one signer.
`verify_checkpoint` returns `False` on **every** defect — malformed key,
malformed signature, genuine mismatch — and never raises. It says nothing
about *which* defect, deliberately: the distinction a reader needs (unknown
signer, unauthorised signer, altered bytes) is drawn one layer up by
`publication.checkpoint_signing`, which has the registry to draw it with. A
primitive that also reported on trust would be two mechanisms wearing one
name.

**The evidence for the primitive changed character, and the honest weak
point is named.** The RFC 8032 §7.1 published vectors — three of them, TEST
1, 2 and 3 — are now the **primary** evidence: they pass against the
provider, and they are the only Ed25519 evidence in the round that does not
share an upstream with it. The out-of-process OpenSSL comparison survives as
**corroboration only**: the oracle is now the `openssl` **command-line
binary** (3.0.13 here), driven through files and exit codes by a script that
imports no cryptographic Python library at all, and it accepts the three RFC
vectors and rejects three mutated-message variants. Its limitation is
stated rather than buried — the CLI and the library the provider links share
an upstream project, so a defect present in both builds would be invisible.
The previous in-process oracle, which called OpenSSL *through
`cryptography`*, was **deleted** once `cryptography` became the provider: it
had become a library compared against itself in one process, which is
agreement by construction and not an oracle at all.

**No constant-time claim follows from any of this.** OpenSSL pursues
side-channel resistance as a design goal for Ed25519, which is a materially
better position than a double-and-add branching on key bits — and it is the
library's design goal, not this repository's measurement. `OD-P16D-05` is
narrowed to exclude the signing surface and stays open.

**The trust anchor is the election context, not the artefact.** A verifier
that accepted a key carried inside the thing it is verifying would let
anyone mint their own board. The authorised signer set is a `SignerRegistry`
fixed before the first checkpoint and supplied *alongside* the export; the
checkpoint carries only a key identifier that must resolve inside it.
`CheckpointPayload` has no `public_key` field at all, and a structural test
asserts no path reads one out of a checkpoint. Rotation is expressed by
declared-in-advance activation windows (`active_from_sequence`,
`active_to_sequence`, `superseded_by`), never by a key announcing itself.

**Authenticity is not consistency, and the two are kept apart
deliberately.** A valid signature proves the named authorised signer issued
this checkpoint. It does not prove the board showed the same checkpoint to
everyone: a dedicated test constructs two checkpoints at one sequence with
different roots and **both signatures genuine**, and `verify_board` returns
`BOARD_INCONSISTENCY`. Conflating the two would be the easiest way to
overclaim here.

What remains open is who authorised the registry itself. The verifier
checks a checkpoint against the registry it was given and cannot tell its
reader that registry was authorised by the Election Board — `OD-P16D-12`,
and the eighth entry in `NOT_CHECKED`.

## External conformance

**Five classes of evidence** (`testing/conformance.py`), named so that the
weakest can never be mistaken for the strongest — and, since the second
audit, so that a cross-check on a group the election will never use cannot
hide behind one on the group it will:

- **internal-stability** — produced here, consumed here. Proves the
  canonical forms have not drifted. Proves nothing about correctness,
  because an error made consistently is invisible to it.
- **primary-source** — a value published externally and reproduced here.
- **rfc-conformance** — a published RFC test vector reproduced by the
  primitive. Split out because an RFC's vectors are the strongest evidence a
  *primitive* can have, and conflating them with protocol-parameter
  provenance made both harder to audit.
- **cross-implementation-test-profile** — computed independently, on
  `EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160`.
- **cross-implementation-target-profile** — computed independently, on
  `EPD2-CRYPTO-1` itself.

The catalogue is `EPD2-CONFORMANCE-2` and holds **26 entries: 1
primary-source, 1 rfc-conformance, 8 cross-implementation-test-profile and
16 cross-implementation-target-profile**, with **zero** internal-stability
entries — the 23 stability vectors stay in their own artefact with their
`stability-only (interoperability NOT established)` status. **The split
promoted nothing.** Every datum that ran on the test profile is still
labelled as such; the target-profile entries are new work.

`tests/reference/test_target_conformance.py` is that new work: **15 tests,
marked `slow_conformance`**, run by one documented command
(`pytest -m slow_conformance services/voting-service/tests/reference/`),
cross-checking **all twelve core operations on `EPD2-CRYPTO-1`** — parameter
digest, group element encoding, scalar encoding, selection encryption,
selection proof, ballot hash, confirmation code, accumulation, guardian
public commitment, decryption share, 3-of-5 combination and aggregate tally
recovery. Every nonce, scalar and plaintext is fixed, because comparing two
independently randomised ciphertexts proves nothing. The fixtures are
**exported** (`PACK-16D-TARGET-PROFILE-FIXTURES.json`, 12 cases,
`contains_secret_material: false`) so a third party can run the comparison
without running EPD²'s suite, and the oracle's verdicts now carry a
machine-readable envelope — `vector_id`, `operation`, `profile_id`,
`expected`, `actual`, `match`, `oracle_version`.

Two details carry more weight than the count. The oracle's `ballot_structural`
handler is handed the ballot's **fields** and rebuilds the canonical bytes
itself: handing it the producer's encoding would test the hash and not the
encoding, and the encoding is where the real defect was. And the two
deliberately invalid fixtures are each tampered by multiplying by `g`, so
they stay **inside** the subgroup and are refused by the mathematics rather
than by a cheap structural check that any random value would also have
tripped.

`PRIMARY_SOURCE_UNAVAILABLE` names six operations for which no published
external vector exists, each with a reason — chiefly that EPD2's canonical
encoding, domain separation and confirmation-code alphabet are EPD2
decisions with no external counterpart. **No self-generated value was
relabelled to fill a gap**, which was the temptation this section exists to
resist.

Calling the same Python function through a different wrapper would not be
independence, and is explicitly not what happens.

## Constant-time limitations

**No constant-time or side-channel claim is made by EPD², and none may be
inferred.** Python's arbitrary-precision integers and `pow()` are not
constant-time; neither the exponentiations nor the comparisons are written
to be. This is stated in `crypto/proofs.py` where a reader of the code will
see it, in the package banner, and in the security-limitations document.

The earlier correction **widened** this rather than softening it. Four
surfaces are distinguished, because one blanket statement let the
secret-bearing paths hide inside it:

| Surface | Secret-bearing? | Status |
| --- | --- | --- |
| public verification (proof, signature, Merkle) | no | timing carries no secret |
| guardian secret operations (DKG, share computation) | **yes** | not constant-time; pure Python |
| secret nonce generation | **yes** | OS CSPRNG; the *use* is not constant-time |
| Ed25519 private-key signing | **yes** | moved to a vetted provider; **risk reduced, nothing measured** |

**The fourth row is the one this round changed, and the change is narrowing,
not closing.** The hand-written scalar multiplication that branched on key
bits is gone, and OpenSSL pursues side-channel resistance for Ed25519 as a
design goal. That is a real reduction in risk. It is **not** an assurance:
EPD² has not measured timing, not run a leakage assessment, and not
inspected the code path the deployed wheel takes, and a library's own design
goals are the library's evidence rather than this repository's.

The other three rows are untouched. The group arithmetic, the NIZK proof
families and every guardian secret operation are still pure Python `int` and
`pow()`, and the guardians are the largest secret-bearing surface in the
system. Fixing that is not a matter of care at this layer: it requires a
constant-time bignum path, which means either widening the dependency policy
again — deliberately, with review — or a different language for the
cryptographic core. `OD-P16D-05` therefore stays **open, narrowed in scope**,
and remains a production blocker.

## Continuation state

Three booleans and a capability reference. `spend_public_challenge()` clears
only the challenge entitlement; `consume_for_cast()` consumes the capability
outright, clearing both. `K = 1`, `A = 1`, `L_max = E × (K + A)`, computed
from the maximum number of valid continuation capabilities and never from
turnout.

A consequence worth stating because a test got it wrong first: a public
challenge published *after* the final cast is not evidence of anything, so a
capability consumed by a cast can no longer challenge. When a cast and a
challenge race, the outcome is therefore order-dependent, and that is
correct rather than a defect.

## Atomic public challenge

One transaction: check idempotency, validate the capability and its
entitlement, verify every proof and the opening, reject a duplicate
artefact, reserve a challenge-eligible leaf, spend the challenge
entitlement, persist the spoiled artefact, commit the reservation, create
the publication obligation. Any exception restores a full snapshot.

A public challenge may take a challenge-reserved slot and then the shared
reserve, and **never** a cast-reserved slot. That holds sequentially and
under a thread race.

## Atomic cast acceptance

The same shape, with the capability consumed **after** the artefact is
durable. A crash at any of the six transactional fault points leaves the
store byte-identical to its pre-call state, the capability unspent and no
leaf slot leaked; a retry then succeeds and lands on the same slot as if
nothing had happened. Two simultaneous casts on one capability yield exactly
one acceptance, one committed leaf and one slot owner.

## Persistence model

Separate maps with **no shared key across the acceptance boundary**: the
continuation map holds no ballot reference and the accepted-ballot map holds
no capability reference. Leaf reservation is compare-and-set over
`(batch_sequence, leaf_index)`. Reservation always precedes durable
acceptance; there is no path that accepts an artefact and then looks for a
slot.

The capacity partition must cover the batch **exactly**. An earlier version
inferred the shared reserve from whatever capacity was left over, which
silently reintroduced adaptive overflow the moment a batch grew;
`CapacityPlan.validate()` now refuses a plan that leaves an unclassified
slot, and `seal_batch()` refuses a batch that cannot hold its committed
reservations.

## Idempotency

Scope is `(election_context_id, operation, idempotency_key)`. The same key
with the same canonical request replays a stable result; the same key with a
different request is a hard conflict, never a silent replay.

**The check runs inside the transaction.** It did not, at first: two
concurrent requests sharing a key could both observe "no record yet" and
both proceed. A concurrency test found it. The code now carries a comment
saying not to move it back out.

## Transactional outbox

Rows carry no capability, credential, identity, trace, correlation id or
exact timestamp. Dispatch is at-least-once: a row is marked `DISPATCHED`
only after the publish step returns, so a crash between the two leaves it
pending and the next sweep retries it. Duplicate suppression is the board's
job — one obligation, one entry — not the outbox's.

## Sealed batch implementation

Three leaf classes. A real leaf is a domain-separated hiding commitment
under a 32-byte salt; a cover leaf is uniform random bytes of the same size,
**not a hash of anything**, with no salt, no reference and no opening. Every
unused slot becomes a cover leaf, so a batch is always exactly its capacity
and its serialised size is independent of occupancy — measured by comparing
an empty batch with a four-ballot batch, not asserted.

## Bulletin board

An append-only log with chained **Ed25519-signed** checkpoints over an RFC
6962 shaped Merkle tree, with inclusion and consistency proofs. The verifier
detects rollback, equivocation, a broken chain, a checkpoint whose root does
not recompute from the exported entries, and now an unauthorised, unknown,
missing, altered or context-mismatched signature — five outcomes with five
distinct exit codes. An export carrying checkpoint tuples but no signed
checkpoints returns `INCOMPLETE_RECORD` rather than quietly falling back to
a weaker digest.

One thing it still does not do, stated here rather than left to be
discovered: it does not detect a split view across mirrors, because that
mechanism remains unstandardised — RFC 9162 §11.3 places gossip out of
scope, RFC 6962 §5 defers it, `draft-ietf-trans-gossip-05` expired in 2020,
and C2SP `tlog-witness` is not ratified `[G-01]`…`[G-05]`. An ad-hoc gossip
protocol would be a security claim nobody has reviewed. Verifying the
signature does not help here and must not be presented as if it did.

## Election record

`open_tally(board_closed)` is a hard gate that takes a boolean and reads no
flag, no environment variable and no configuration — asserted by a test that
inspects its signature and its source. Reconciliation enforces one artefact
to one leaf, no cover leaf in the tally, `accepted ≤ E` and `spoiled ≤ E × K`.
The record's canonical bytes cover the batch openings and the decryption
shares; an earlier version omitted both, so the digest did not commit to
them.

## Reference verifier

Public artefacts and exported bytes only. **26 result codes with 26 distinct
exit codes**, and a `NOT_CHECKED` list of **nine** limits printed with
**every** result, including `VERIFIED` — among them that `VO-08` is open.
Seven codes are unreachable through `verify_record` this round; each is
named with its reason in the test suite rather than left as an unexplained
gap.

The `NOT_CHECKED` list shrank by one entry and grew by two. "Checkpoint
signatures are never verified" was **removed because it became false**, and
a stale limitation is worse than none: a reader who finds one entry
outdated has no way to know which of the others still hold. It was replaced
by two narrower statements that are true — that the verifier cannot vouch
for the signer registry it was given (`OD-P16D-12`), and that a valid
signature is never evidence of a single view.

Two codes are new for the ceremony (`INVALID_CEREMONY_TRANSCRIPT`,
`GUARDIAN_QUORUM_MISMATCH`) and five for signatures
(`BOARD_SIGNATURE_MISSING`, `BOARD_SIGNER_UNKNOWN`,
`BOARD_SIGNER_UNAUTHORIZED`, `BOARD_SIGNATURE_INVALID`,
`BOARD_SIGNATURE_CONTEXT_MISMATCH`). The five are deliberately distinct
rather than one `INVALID`: "nobody signed this", "the wrong person signed
it" and "the bytes were altered" are different incidents demanding
different responses, and collapsing them would cost an operator the one
piece of information they need first.

Ceremony verification runs **immediately after the joint-key subgroup check
and before anything that uses the key**. Ordering matters here for a reason
found by test: with the check placed later, a record with a tampered
ceremony returned `INVALID_BALLOT_PROOF` — technically true, and it would
have sent an investigator to the wrong place entirely.

## Test vectors

23 vectors across the 20 families §38 names. **Every one is self-generated
on a TEST profile**, and the catalogue's `source` and `status` fields say so
verbatim. They prove determinism and stability — a change to the encoding,
domain separation, hashing or a proof transcript breaks regeneration. They
prove nothing about agreement with any other implementation, and two tests
fail if a vector's provenance is softened or a production profile is
claimed.

The first candidate presented these as this round's conformance evidence.
They are not, they never were, and the classification in *External
conformance* above exists so the distinction survives the next reader.
`OD-P16D-02` — comparison against a *complete* independent implementation —
remains open and is owned by PACK-17. It no longer depends on
`OD-P16D-01`.

## Negative corpus

39 cases, each asserting the specific reason code it expects rather than
merely that something was raised — and a guard test that fails if any case
weakens to a type-only assertion. Four declared codes turned out not to
match what the implementation raised; the index was corrected to reality.
Three cases are new this correction: `ambiguous_sequence_encoding`,
`unauthorized_board_signer` and `insufficient_guardian_quorum`.

## Concurrency testing

Nine races, twelve repeats each, real OS threads released from a barrier.
The five §42 expectations are asserted directly. This proves the *logic* is
race-free under the reference store's re-entrant lock; it proves nothing
about a production datastore, where the same invariants must come from
row-level locking or a serialisable isolation level. That is `OD-P16D-04`.

## Fault injection

Eleven points. Six sit inside a transaction and must leave the store
byte-identical; five sit outside one, where the correct property is
recoverability rather than rollback, and each is asserted for what it
actually leaves behind. Production code depends only on a `FaultHook`
protocol and a hook can arrive only by being passed explicitly into a call,
so a deployed system that never passes one cannot have a fault injected. A
test parses every production module with `ast` to prove none imports the
injector.

## Logging boundary

23 forbidden field names, 7 allowed, and **no redaction step**: a forbidden
field is a defect in the caller, so the record is refused and nothing is
written. Free-text reason codes are refused too, because a field-name
boundary cannot detect a capability smuggled inside prose. Audit evidence is
a hash chain of ten record types that accepts no additional fields; role
restriction and retention are governance properties named here and **not
implemented**.

## Rejected alternatives

| Alternative | Why rejected |
| --- | --- |
| A vetted native cryptographic library **for the group arithmetic** | Would give a constant-time bignum path for the guardian and proof surfaces, and would require widening the dependency policy again for a library this round could not assess. Deferred deliberately rather than taken quietly. **This row no longer covers signatures**: one vetted provider was adopted for that primitive, assessed in `PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md` §2.1 and §3 |
| A new `uv` workspace member for the reference package | Would require a workspace-level manifest change on top of the lock regeneration. The reference package therefore lives inside `epd2-voting-service`, and adding a dependency to that package's own `pyproject.toml` was the smaller change. That dependency is now resolved in `uv.lock`; the workspace shape is unchanged |
| Canonical JSON as the wire encoding | Canonical JSON specifies how to avoid a format's ambiguities. A format without them is simpler to verify |
| Duplicating the last node on odd Merkle levels | The shape where two different leaf sequences share a root. Replaced with RFC 6962, not patched |
| Substituting a same-size test group for `EPD2-CRYPTO-1` | Would make every test green and every result meaningless. `EPD2-TEST-P4096-Q256` had the right *shape* and neither the family's `r/2`-prime property nor its `ln(2)` derivation. Renamed to `EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256` so the name cannot invite the substitution the code forbids |
| A fallback when `EPD2-CRYPTO-1` fails to load | Any fallback — `except`, default argument, environment variable, feature flag — converts a loud failure into a silent downgrade. `load_profile` has none, proved structurally rather than by review |
| Replacing the profile with a reduced group because the real one is slow | 28.12 s for `test_epd2_crypto_1` and 8.06 s for the target-profile core is the honest cost of 4096-bit arithmetic in Python. The runtime is recorded, exported next to the fixtures, and the test partitioning optimised; the group is not touched |
| **Keeping the hand-written Ed25519** because it passed the RFC 8032 vectors and agreed with OpenSSL | This is the argument the previous round made, and it is wrong. Passing the vectors an author thought to write says nothing about the vulnerability class the author did not think of — a missing subgroup check, a branch that leaks a key bit, a non-canonical encoding accepted on an untried input. Those are found by years of adversarial attention on one widely deployed implementation and cannot be found by the author of a fresh one. `crypto/ed25519.py` is deleted, not kept "for reference": a file one import away from being active is still from-scratch curve code in the repository |
| **A `try: import cryptography / except: use our own` fallback** | It would silently reinstate the removed implementation on whichever machine lacked the dependency — and that is precisely the machine you would least want running hand-rolled cryptography. The provider imports at module scope and raises `SignatureProviderUnavailableError` if the library is absent. Failing closed at import is the whole point, and a test runs a subprocess with the library blocked to prove it, with a control run first so the test cannot pass by accident |
| **Hand-editing `uv.lock` to add the provider** | Prohibited, and for a concrete reason rather than a stylistic one: a `[[package]]` entry needs a registry source and distribution hashes for artefacts that were never downloaded. Typing plausible hashes produces a file that looks resolved and is not, and the failure surfaces at the worst possible moment. The gap was left declared and open for two rounds instead, and was closed by the resolver — `test_uv_lock_was_not_hand_edited_to_fake_the_provider` asserts the entry has the shape a resolver produces |
| **Pinning the parameter source to the `/main/` URL** and calling it provenance | A branch reference is a moving target, and the audit was right to call it `PARTIAL`. The authoritative reference is now a versioned release asset with its digest in the artefact, the Rust file is demoted to corroborating with `human_readable_url_is_authoritative: false`, and the values are established independently of both by offline reconstruction. The digest previously recorded for that file was withdrawn rather than relabelled, because it was computed over a markdown rendering |
| Carrying the signing public key inside the checkpoint | Then anyone can mint their own board. The trust anchor must arrive out of band, which is why `CheckpointPayload` has no key field at all |
| Compensated decryption for a missing guardian | Prohibited by the PACK-16B baseline. The function exists only to refuse, so the prohibition is discoverable in code rather than only in a document |
| Letting the caller supply the quorum to `combine_shares` | A caller-supplied `k` is threshold reduction with extra steps. The quorum comes from the ceremony transcript, and a rewritten transcript fails verification |
| Reusing the internal-stability vectors as conformance evidence | The first candidate did this and the audit was right to fail it. A self-generated vector cannot detect a consistent error — as `encode_seq` proved |
| Calling the same Python functions through a second wrapper as a "cross-check" | Agreement by construction. The oracle had to re-derive the encoding from the grammar, which is precisely why it disagreed and found a real defect |
| Inferring the shared reserve from leftover batch capacity | Silently reintroduces adaptive overflow whenever a batch grows |
| Redacting forbidden fields in logs instead of refusing them | Redaction turns a caller defect into a passing test |
| Verifying consistency proofs by re-running the prover's recursion | A verifier that mirrors the prover agrees with it by construction and proves nothing |

## Residual risks

**Closed by this correction.** Three, and each names a finding rather than a
preference:

- `OD-P16D-13` — the hand-written signature primitive. **CLOSED**: a vetted
  provider, with the from-scratch implementation deleted.
- `OD-P16D-14` — the mutable parameter source reference. **CLOSED**: the
  authoritative reference is a versioned release with its digest in the
  artefact, plus offline reconstruction of the whole parameter set.
- `OD-P16D-15` — target-profile cross-check coverage. **CLOSED**: all twelve
  core operations, on `EPD2-CRYPTO-1`.

**Narrowed and still open.** `OD-P16D-05` — the signature surface moved to a
library that pursues side-channel resistance. **EPD² has measured nothing**,
and the group arithmetic, the proofs and every guardian secret operation
remain pure Python. This is still a production blocker.

**Opened by an earlier correction and now closed**, on recorded command
output rather than on assertion:

- `OD-P16D-16` — the provider was declared and not locked. `uv.lock` now
  resolves `cryptography 46.0.7` with artefact hashes, inside the
  `epd2-voting-service` graph. **CLOSED.**
- `OD-P16D-17` — the corroborating upstream source was not commit-pinned. It is
  pinned at `5206511…ceac` with a raw-byte digest recorded in the parameter
  artefact. **CLOSED.** The earlier withdrawn digest was not restored.

**Unchanged and open**, carried without change of meaning or state:

1. The reference key ceremony has no custody model (`OD-P16D-11`): one
   process, no authenticated channel, no HSM, no air gap, no witnesses.
2. The signer registry's own authorisation is outside the verifier's reach
   (`OD-P16D-12`).
3. No comparison against a *complete* independent implementation
   (`OD-P16D-02`). Two single-purpose oracles are not one, and one of them
   now shares an upstream with the primitive it checks.
4. Concurrency evidence covers one in-memory store (`OD-P16D-04`).
5. Property tests do not shrink or search adversarially (`OD-P16D-03`).
6. No split-view detection across mirrors (`OD-P16D-06`).
7. No production authentication (`OD-P16D-08`).
8. The reference tally handles one ballot style (`OD-P16D-10`).

**Standing residuals that no round closes by itself:**

9. No secret-material zeroization; Python cannot reliably do it.
10. No nonce-reuse detector — a caller passing the same nonce twice is not
    caught, though a context-bound proof does not transfer.
11. `is_probable_prime()` is Miller–Rabin, not a proof of primality — which
    matters more now that it is applied to the real `p`, `q` and `r/2`.
12. A compiled native artefact is now in the runtime path. Its resolution is
    hash-pinned in `uv.lock`, which fixes *which* bytes are installed; it says
    nothing about how that implementation behaves under timing observation, and
    a libcrypto advisory remains an EPD² concern.
13. Branch coverage was not measured; no tool is installable here.
14. `VO-08` is open: having the published parameters is not having an
    assessment that they are appropriate for a binding German election.

**Never closed by any round of PACK-16D**: external cryptographic review, a
complete independent verifier, a production HSM, a production key ceremony,
formal verification, legal assessment, `VO-08`, and production deployment.

## VO-08

**OPEN.** Owned by PACK-16B external cryptographic review, with independent
confirmation in PACK-17. PACK-16D does not close it, does not narrow it and
does not re-own it. No BSI conformity is claimed. `VO-08` is carried into
the implementation acceptance gates and named in the verifier's
`NOT_CHECKED` list, so every verification result — including a passing one —
tells its reader that the parameters have not been assessed.

**Obtaining the parameters did not narrow `VO-08` by one word.** The
temptation to treat "we now have the published constants and they check out
arithmetically" as partial progress on a BSI assessment is exactly the
error this section exists to prevent. `VO-08` asks whether this parameter
family is appropriate for a binding German public election. That is a
question for an assessor, and no amount of local verification answers it.

## Consequences for PACK-17

PACK-17 inherits **eleven open decisions** — `OD-P16D-02`, `-03`, `-04`,
`-05`, `-06`, `-08`, `-10`, `-11`, `-12`, and the two this correction
created, `-16` and `-17` — one of them a production blocker, and a harness
to attack rather than a specification to read.

The two smallest of these — the dependency lock and the upstream commit pin —
have been discharged on a network-enabled host and are recorded above. Neither
was cryptographic work; both were environmental, and both are the kind of gap
that makes a round look less finished than it is while changing nothing about
what the code does.

PACK-17 must: obtain conformance evidence from a **complete**
independent ElectionGuard 2.1 implementation in both directions
(`OD-P16D-02`); obtain an Ed25519 oracle that shares no upstream with the
provider, since the CLI comparison no longer supplies one; specify a real
key ceremony with custody, authenticated channels, HSM-backed generation and
witnesses (`OD-P16D-11`); establish how a signer registry is published and
authenticated independently of the board (`OD-P16D-12`); re-run the nine
races against a production data plane with the isolation level named
(`OD-P16D-04`); convert the property tests to hypothesis strategies
(`OD-P16D-03`); obtain **measured** timing evidence, or a constant-time
implementation, for the guardian and proof surfaces (`OD-P16D-05`); choose a
witness or gossip mechanism against a published standard (`OD-P16D-06`);
implement multi-style tallying (`OD-P16D-10`); and re-run every command in
this round through `uv run` with the pinned tool versions, since this round
could not.

## Production blockers

```text
VO-08 open - the parameters are present but not assessed
constant-time production assurance - BLOCKED; the signing surface moved
  to a vetted provider, nothing was measured, and the group arithmetic,
  proofs and guardian secret operations are still pure Python
no key custody: the ceremony runs in one process, and the checkpoint
  signing seed is ordinary process memory
no production authentication or credential integration
no HSM or key-storage boundary
no production data plane; concurrency proven only in memory
no comparison against a complete independent implementation
external cryptographic review - BLOCKED
no legal assessment
```

## Canon impact

**`NO CANON CHANGE REQUIRED`.**

```text
CANON_VERSION remains 0.8.0.

No Canon domain, aggregate, event or invariant semantics changed.

Canon compatibility metadata continues to support
repository version 0.16.x.
```

All eight entities §54 names map onto aggregates PACK-16A/16B/16C already
specified. Implementation types — including the guardian records, threshold
shares and checkpoint signer records, and this correction's
`CheckpointSignatureProvider` and `CryptographyEd25519Provider` — are held at
service level on the precedent PACK-12's `PrivilegedSession`, PACK-14's
`SessionRecord` and PACK-15's voting context registry set. A signature
provider and a parameter-provenance block are implementation concerns; they
introduce no domain vocabulary.

The third line above is precise, and its precision is deliberate. **It does
not say the canon files were untouched, because that would be false.**
`docs/canonical/canon-version.json` was modified in the `0.16.0` round: its
non-canonical `repository_compatibility` was widened from `>=0.1.0 <0.16.0`
to `>=0.1.0 <0.17.0`. That change is correct and is not reverted. **This
correction modified no file under `docs/canonical/`.** Describing a modified
file as untouched is the kind of small inaccuracy that costs a reader their
trust in everything else the document says, which is why the line states
what the metadata continues to support rather than what was or was not
edited.

## FIR impact

`FIR-ROADMAP-006` reaches **`implemented in reference form`, partially**,
and keeps its register status `approved`: items in its scope — audited
protocol integration, a production data plane, and a production key
ceremony — are not delivered by a reference implementation. `FIR-INV-002`
remains **partially implemented** and is **not closed**. `FIR-ASM-006` and
`FIR-ASM-007` reach **test harness complete**. `FIR-TRUST-001` moves to
**partially implemented**: the signature half of the signature-and-timestamp
framework now exists; the timestamp half does not. `FIR-SEC-002` stays
**blocked pending external review** — the parameters arrived, the assurance
did not, and assurance is what the entry is about. `FIR-ROADMAP-007`,
`FIR-SEC-001` and `FIR-OSS-006` are **deferred to PACK-17**.

**New FIR IDs: none. FIR statuses changed: none.** None of the eight items
§55 forbids closing was closed.

---

**Status: `proposed`. This ADR accepts no earlier ADR, claims no
conformity, and is not a PASS. PACK-17 must review before production
acceptance.**
