# PACK-16D — Parameter Profile Implementation

**Round:** PACK-16D — Network-Enabled Finalization: Lockfile Regeneration,
Immutable ElectionGuard Provenance and Final Acceptance Alignment.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The target profile loads

This is the first thing a reader must know about this round, so it is the
first section.

`EPD2-CRYPTO-1` — the ElectionGuard 2.1 published 4096-bit family, which
PACK-16B named as the intended production profile — **is the target
profile and it loads**. Its constants live in the artefact
`services/voting-service/src/epd2_voting_service/reference/crypto/profiles/EPD2-CRYPTO-1.json`,
and the whole reference stack can be run on them.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                              |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-01` | The artefact's **authoritative source** is a specification, not a branch: the **ElectionGuard Design Specification**, version `2.1.0`, section `3.1.1, page 14`, "Standard Baseline Cryptographic Parameters". The full structure of the provenance block, and the reason a specification rather than a source file is the authority, are in §1.4 |
| `PP-02` | The constants `p` (4096 bits), `q` (256 bits), `g` and the cofactor `r` are stored as **canonical lower-case fixed-width hex with no separators**, so two readers cannot disagree about a value. `load_profile()` rejects anything that is not that form                                                                                          |
| `PP-03` | `parameter_digest = sha256(p_hex \|\| q_hex \|\| g_hex \|\| r_hex)` is **`f0af5b71412ccf93a1eaf93364c223f5339cdb2815a2efcfa1bd775cd2bf17fb`**. It is carried in the artefact **and** pinned in code as `EPD2_CRYPTO_1_PARAMETER_DIGEST`, so editing the artefact is detected rather than absorbed                                                 |
| `PP-04` | The separate canonical-encoding digest of the loaded `ParameterSet` — `ParameterSet.digest_hex()`, taken under `DomainLabel.PARAMETER_SET` — is `8031fb86b229c104585499aef1405d52e623900f5626d9f7690ad8f62ffc4c60`                                                                                                                                |
| `PP-05` | `load_target_profile()` is the only entry point a conformance run may use, and `require_target_profile(params, what)` raises `ProfileSubstitutionError` (`PARAMETER_SET_NOT_APPROVED`) for anything that is not `EPD2-CRYPTO-1`                                                                                                                   |

### 1.1 The transcription was verified by arithmetic, not by trusting the fetch

Fetching 1024 hex digits and believing them is not evidence. Every relation
below is checked against the loaded constants, and **a single wrong hex
digit anywhere breaks at least one of them**:

```text
|p| = 4096                       |q| = 256
q = 2^256 - 189                  q | (p - 1)
p = q * r + 1                    1 < g < p,  g != 1,  g^q = 1 mod p
p probable prime                 q probable prime      r/2 probable prime
p's leading 256 bits all ones    p's trailing 256 bits all ones
p's middle 3584 bits agree with ln(2) for 3306 of 3584 bits
p reconstructs from the ln(2) rule and delta   g = 2^r mod p   r = (p-1)/q
```

The last line is the reconstruction of §1.5, and it is the strongest of
these checks: the others confirm relations _between_ the published
constants, while the reconstruction produces the constants from the rule.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `PP-06` | **The `r/2`-prime property and the `ln(2)` derivation are the published family's documented structure**, and they are what distinguish these constants from a same-sized substitute. The first candidate's 4096/256 test profile had **neither**, which is exactly why it was never a stand-in                                                                                                                                                                                                                                                         |
| `PP-07` | `test_epd2_crypto_1_structural_provenance` in `services/voting-service/tests/reference/test_epd2_crypto_1.py` computes `ln(2)` on the spot from `2·atanh(1/3)` and compares it against `p`'s middle bits; `test_epd2_crypto_1_subgroup_relation`, `test_epd2_crypto_1_generator_order`, `test_epd2_crypto_1_p_bits` and `test_epd2_crypto_1_q_bits` pin the rest. `test_epd2_crypto_1_invalid_constant_rejected` alters a single hex digit of `g` and asserts both that the artefact's self-digest stops matching and that the subgroup relation fails |
| `PP-48` | **No document in PACK-16D transcribes `p`, `q`, `g` or `r`.** The artefact is the one place the constants live; the documents carry the digests and the relations                                                                                                                                                                                                                                                                                                                                                                                      |

### 1.2 There is no fallback

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                       |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-49` | **No substitution of any kind exists.** There is no default profile, no fallback profile and no "nearest shape" resolution. `load_profile` reads exactly the artefact named by the profile id; `test_loader_source_names_no_fallback_branch` inspects its source and asserts it contains no `except`, no `TESTONLY` and no `default`                                       |
| `PP-50` | **No environment variable and no feature flag can redirect the loader.** `test_epd2_crypto_1_no_environment_or_flag_can_substitute` sets four environment variables to a test profile id, asserts `load_target_profile()` still returns a 4096-bit `p`, and asserts that a `disable_parameter_validation` feature flag is refused at startup with `UnsafeFeatureFlagError` |
| `PP-51` | An unregistered identifier fails closed through the same door: `load_profile("EPD2-CRYPTO-1-BUT-FASTER")` raises `ParameterProfileUnavailableError` (`PARAMETER_SET_NOT_APPROVED`). Unknown and unavailable are both closed, and neither is silent                                                                                                                         |
| `PP-52` | **`production_use_permitted` is `False` on every profile `load_profile()` can return**, including the target. The field is set to `False` unconditionally in `load_profile()`; there is no argument, no environment variable and no configuration that sets it `True`. Loading the published parameters is not authorisation to run an election on them                    |

`OD-P16D-01` — "the target profile is unavailable" — is **CLOSED** by this
correction. What remains open about parameters is `VO-08` and the external
cryptographic review (§5), which are different questions: whether the
parameters are _appropriate_ and who says so, not whether they load.

### 1.3 What IS asserted first-hand about the small prime

`Q_ELECTIONGUARD_2_1: Final[int] = 2**256 - 189` is defined in
`crypto/parameters.py` as arithmetic, not as a transcribed literal, so it
cannot carry a transcription error.

`test_q_is_the_electionguard_small_prime` asserts all three of:

- `Q_ELECTIONGUARD_2_1 == 2**256 - 189`
- `Q_ELECTIONGUARD_2_1.bit_length() == 256`
- `is_probable_prime(Q_ELECTIONGUARD_2_1)` — probable, in the sense of §5

### 1.4 The provenance block, restructured

The audit finding was
`PARAMETER SOURCE REPRODUCIBILITY: PARTIAL — MUTABLE URL / DIGEST NOT IN
ARTIFACT`. It was right. The previous artefact named a `/main/` URL, which
is a moving target, and recorded a digest that could be mistaken for a
digest of that file. `EPD2-CRYPTO-1.json` now carries four blocks that
answer four different questions, and they are kept apart deliberately.

| ID      | Block                  | What it is for                                                                                                                                                                                                                                                                                    |
| ------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-57` | `source.authoritative` | The **specification** — `kind: "specification"`, title `ElectionGuard Design Specification`, version `2.1.0`, section `3.1.1, page 14`. Its `document_url` is a **versioned release asset** under the tag `v2.1`, not a branch reference, and the artefact says so in `document_url_immutability` |
| `PP-58` | `source.corroborating` | The published reference implementation source — the Rust file — explicitly **not** authoritative, and explicitly **not** commit-pinned. §1.6                                                                                                                                                      |
| `PP-59` | `digests`              | Two digests that must never be confused, each with its own definition string. §1.7                                                                                                                                                                                                                |
| `PP-60` | `derivation`           | The offline reconstruction. §1.5, and it is the strongest thing in the artefact                                                                                                                                                                                                                   |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-61` | **`document_sha256` for the specification is `a263ab3cd2cf28f05de324ecd2d9752ffed45f814709582b4c2bb23d1826b936`, and it was NOT re-verified this round.** It is inherited from PACK-16B evidence F-01, where it was recorded first-hand. It could not be re-checked here because the document could not be retrieved in this environment. The artefact states this in `document_sha256_provenance` rather than presenting the value as freshly confirmed, and this document repeats it rather than letting the reader assume |
| `PP-62` | **The authoritative reference is a specification rather than a source file on purpose.** A source file is one implementation's reading of the parameters; the specification is what every implementation is reading. Pointing the authority at the specification also means the authority does not move when a repository's default branch does                                                                                                                                                                              |

### 1.5 The offline reconstruction — the centrepiece

This is the strongest evidence in the artefact, and it is stronger than any
URL could be. A URL says where the bytes came from. **This says the bytes
are the ones the published rule produces.**

The whole parameter set is rebuilt from the published structural rule with
**no file and no network**:

```text
p          = ONES(256) || M(3584) || ONES(256)          4096 bits total
M          = (first 3305 fractional bits of ln 2) << 279 | delta_low
delta_low  = 0x445744fb5f2da4b751005892d356890defe9cad9b9d4b713e06162a2d8fdd0df2fd608
             (279 bits)
q          = 2**256 - 189
r          = (p - 1) // q
g          = pow(2, r, p)
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-63` | **`ln 2` is computed locally, not tabulated.** The artefact's `p_middle_rule` states the series: `2·atanh(1/3) = 2·Σ_{k≥0} (1/3)^(2k+1)/(2k+1)`. No table is consulted and no network access is used, so the reconstruction cannot inherit an error from a copied constant                                                                                                                                                                   |
| `PP-64` | **Only one constant has to be recorded: the 279-bit `delta_low`.** Everything above it in `p` is `ln 2`; everything around it is the two 256-bit runs of ones. `q` is arithmetic. `r` and `g` then follow **in closed form** — `r` is a division and `g` is a single modular exponentiation of the base 2 — so they are not independent data at all and cannot be transcribed wrongly without failing                                        |
| `PP-65` | **All four constants reconstruct exactly**, and the artefact records `reconstruction_verified_offline: true`. A transcription error anywhere in `p`, `q`, `g` or `r` fails reconstruction; there is no partial agreement to argue about                                                                                                                                                                                                      |
| `PP-66` | **This is what made the missing upstream digest survivable while it was missing, and it is what keeps the recorded one in proportion now.** The parameter values are established by the rule and by the arithmetic of `verification_performed`, neither of which depends on the corroborating file or on any network access. The commit pin adds a trail a reader can walk; it does not become the thing the values rest on                  |
| `PP-67` | Two numbers in the artefact look similar and are not the same measurement. `derivation.ln2_prefix_bits` is **3305** — the number of fractional `ln 2` bits the reconstruction rule consumes. `verification_performed.p_middle_bits_match_ln2_prefix` is **3306** — the count of `p`'s 3584 middle bits that a prefix comparison against `ln 2` finds equal. The first is the rule; the second is an independent observation about the result |

### 1.6 The upstream commit SHA could not be obtained, and the old digest was withdrawn

Stated plainly, because burying it would be the failure mode this section
exists to avoid.

| ID       | Statement                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `PP-68`  | **The corroborating Rust source is commit-pinned.** For two rounds it could not be: four access paths were refused by two distinct mechanisms and the artefact carried three explicit `null`s rather than absent fields, so a reader could not mistake "not recorded" for "not applicable". The pin was obtained on a network-enabled host — commit `520651138110a13f777409e96606454df928ceac` of 2025-02-02, path `src/eg/src/standard_parameters.rs`, raw-byte SHA-256 `ad38bfa68d31131a7d721e08d359224b21e967aae4d517534a60a109e10f5770`, retrieved 2026-08-03 — and the failing transcripts remain in `PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md` as a `HISTORICAL FINDING` |
| `PP-68a` | **`IMMUTABLE UPSTREAM IMPLEMENTATION PROVENANCE: RECORDED`**, and the artefact says so in `source.corroborating.provenance_status`. Both halves are pinned: the **normative** one to a versioned release asset with its digest in the artefact, the **implementation** one to a commit with its raw-byte digest. They are recorded separately and neither stands in for the other — averaging the two into a single pass is what `AM-79` once did wrong, and two pins do not license doing it again                                                                                                                                                                            |
| `PP-69`  | **The previous round's `3afa2962…` digest was WITHDRAWN, not relabelled.** It was computed over a **markdown rendering** of the file, not over the file's raw bytes, so it was never a digest of what it appeared to be a digest of. Keeping it under a softer caption would have left a wrong number in an artefact that a verifier is invited to trust. Removing it leaves an honest `null`                                                                                                                                                                                                                                                                                  |
| `PP-70`  | **The artefact says who computed the digest, not merely what it is.** `source.corroborating.source_sha256_verification_scope` records that the value was produced on a network-enabled host, that the build session checked the pin's internal consistency and re-derived every parameter offline, and that it did **not** re-fetch the upstream bytes. An auditor closes that last step in one command: `curl -sL <pinned-url> \| sha256sum`                                                                                                                                                                                                                                  |
| `PP-71`  | **`OD-P16D-17` is `CLOSED`** on the pin above. `unpinned_reason` and `auditor_action` were removed in the same change that added it — `test_epd2_crypto_1_source_commit_present` fails if a pin and an excuse for having no pin are ever both present                                                                                                                                                                                                                                                                                                                                                                                                                          |

#### Why a `/main/` URL is kept at all

The artefact still carries
`https://raw.githubusercontent.com/microsoft/electionguard-rust/main/src/eg/src/standard_parameters.rs`,
and next to it `human_readable_url_is_authoritative: false`.

| ID       | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-71a` | **The source hierarchy is now declared explicitly, not left to be inferred from field names.** `source.hierarchy` names three levels — normative specification, corroborating implementation source, local immutable artefact — and `source.corroborating.role` states that it "is NOT a substitute for the normative specification and is not authoritative for any value here". `is_normative` is `true` on one and `false` on the other. The failure mode this guards against is subtle: a reader who treats a reference implementation's source file as normative will accept a value the specification does not actually publish |
| `PP-71b` | **Pinned or unpinned, nothing rests on it.** The parameter values rest on the normative specification and on the offline reconstruction in `derivation`, neither of which consults the Rust file. That is why the gap cost _traceability_ and not _correctness_ — and why closing it raises `AM-79` to `SATISFIED` without changing anything about how much confidence the numbers themselves deserve                                                                                                                                                                                                                                 |
| `PP-72`  | **The `/main/` URL is kept because a human reader needs somewhere to look, and deleted authority is not the same as deleted usefulness.** A reviewer who wants to read the constants in their upstream context can follow it today. What was removed is its _standing_: `human_readable_url_note` says a `/main/` reference is mutable, is recorded for a human reader only, and is never the reference a verifier should rely on. Marking it non-authoritative is a stronger statement than deleting it, because a deleted URL leaves the next round free to re-add one without the caveat                                           |

### 1.7 `parameter_digest` and `source_sha256` are different questions

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-73` | **`parameter_digest` is over the local canonical parameter tuple**: `sha256(p_hex \|\| q_hex \|\| g_hex \|\| r_hex)`, lower-case fixed-width hex, no separators. It is **unchanged** at `f0af5b71412ccf93a1eaf93364c223f5339cdb2815a2efcfa1bd775cd2bf17fb` and is still pinned in code as `EPD2_CRYPTO_1_PARAMETER_DIGEST` (`PP-03`)                                                                           |
| `PP-74` | **`source_sha256` is over the upstream file's exact bytes** at the pinned commit, and `source_sha256_status` says so and names the file. The `digests` block carries a definition string for each of the three digests it holds, so `parameter_digest`, `source_sha256` and `specification_sha256` cannot be read as versions of one another — which is exactly the confusion the withdrawn digest depended on |

## 2. The two TEST profiles, renamed so they cannot be mistaken for the target

Two profiles were generated and self-verified so that the fast paths of the
reference implementation could be exercised without a 4096-bit
exponentiation in every test. Both are TEST profiles. Neither is, or may
become, a production default, and neither may stand in for
`EPD2-CRYPTO-1`.

They were **renamed** in this correction, because a name is what a reader
sees in a log line or a vector file:

| ID      | Profile                                  | \|p\| | \|q\|                 | Properties verified in this round                               |
| ------- | ---------------------------------------- | ----- | --------------------- | --------------------------------------------------------------- |
| `PP-08` | `EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256` | 4096  | 256, `q = 2²⁵⁶ − 189` | `q \| p−1`, `g^q ≡ 1 mod p`, `1 < g < p`                        |
| `PP-09` | `EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160` | 1024  | 160                   | the same three, **plus** probable-primality of both `p` and `q` |

Both files live in
`services/voting-service/src/epd2_voting_service/reference/crypto/profiles/`
and both now open with the same four-line banner, reproduced here verbatim
because it is the profile's own statement about itself:

```text
# TEST ONLY
# NOT EPD2-CRYPTO-1
# NOT ELECTIONGUARD 2.1 CONFORMANCE
# NOT PRODUCTION
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-10` | **`EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256` shares only the _dimensions_ of `EPD2-CRYPTO-1` and is not those constants.** It reuses the small prime `q = 2²⁵⁶ − 189`, which is arithmetic and therefore reproducible; its `p` and `g` are this round's own and have no relationship to the published family                                                                               |
| `PP-11` | **It lacks the published family's r/2-prime property**, and it lacks the `ln(2)` derivation. Nothing in `validate_parameter_set()` checks either property, and this profile was not constructed to have them. A reader must not treat 4096/256 shape as evidence of ElectionGuard-family structure — which is precisely why the shape alone was never accepted as a substitute (`PP-06`) |
| `PP-12` | **`EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160` is cryptographically inadequate by construction.** Its purpose is that property and concurrency tests finish in seconds. It has no other purpose                                                                                                                                                                                              |
| `PP-13` | `TEST_ONLY_MARKER = "TESTONLY-NOTCONFORMANT"` is declared in `crypto/parameters.py`, and `test_epd2_crypto_1_no_fallback` asserts that **every** registered profile id other than the target contains it — so a new test profile cannot be added under an innocuous name                                                                                                                 |
| `PP-14` | Existence and shape are pinned by `test_test_profiles_validate_fully` and `test_p4096_profile_has_the_electionguard_small_prime`                                                                                                                                                                                                                                                         |

### 2.1 Profile artefact formats

The target profile is a JSON artefact; the two test profiles remain flat
`.params` files. Both are read by `_read_profile_artifact()`, which has no
search path, no fallback and no defaulting.

| ID      | Rule                                                                                                                                                                                                                                                                         |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-15` | In a `.params` file, one `name=value` assignment per line; the value is a **decimal** integer parsed with `int()`. In the JSON artefact the constants are **canonical lower-case hex** strings (`PP-02`) and are rejected if they are anything else                          |
| `PP-16` | Blank lines and lines beginning with `#` are ignored in a `.params` file, which is what makes the banner possible                                                                                                                                                            |
| `PP-17` | `p`, `q` and `g` are all required. A file missing any of them raises `ParameterValidationError` naming the missing keys — the file is never partially accepted. The JSON artefact additionally requires `r`, `parameter_digest` and a `profile_id` that matches the filename |
| `PP-18` | A missing artefact is `ParameterProfileUnavailableError`, and the message includes the registry entry, so the reason a profile is absent travels with the failure                                                                                                            |
| `PP-19` | The artefacts contain **public group parameters only**. No private key, guardian secret, credential or member data exists in them or anywhere else in the tree                                                                                                               |

## 3. `validate_parameter_set()` — the ordered check sequence

A parameter set is **never trusted by identifier**. Every load runs the
full sequence. The order is normative because each later check assumes the
earlier ones held, and because the first violation is the one reported.

| ID      | #   | Check                                                    | Raised message                               |
| ------- | --- | -------------------------------------------------------- | -------------------------------------------- |
| `PP-20` | 1   | `p.bit_length() == expect_p_bits`                        | `\|p\| = <n>, expected <m>`                  |
| `PP-21` | 2   | `q.bit_length() == expect_q_bits`                        | `\|q\| = <n>, expected <m>`                  |
| `PP-22` | 3   | `p > 2` and `q > 2`                                      | `p and q must exceed 2`                      |
| `PP-23` | 4   | `(p − 1) mod q == 0`                                     | `q does not divide p - 1`                    |
| `PP-24` | 5   | `1 < g < p`                                              | `g is outside (1, p)`                        |
| `PP-25` | 6   | `g^q ≡ 1 (mod p)`                                        | `g^q != 1: g is not in the order-q subgroup` |
| `PP-26` | 7   | `is_probable_prime(q)`, only when `check_primality=True` | `q is not prime`                             |
| `PP-27` | 8   | `is_probable_prime(p)`, only when `check_primality=True` | `p is not prime`                             |

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-28` | **Fail closed on the first violation.** Every check raises `ParameterValidationError` (`reason_code = "PARAMETER_SET_INVALID"`) immediately. The function has no partial-success return: it returns the candidate unchanged or it raises                                                                                                                                                                                                                                              |
| `PP-29` | Check 6 establishes that `g` lies **in** the order-`q` subgroup. It does not establish that `g` has order exactly `q` — an element of order 1 would also satisfy `g^q ≡ 1`, which is why check 5's exclusion of `g = 1` is load-bearing and is placed before it                                                                                                                                                                                                                       |
| `PP-30` | Checks 1 and 2 come first so that a wrong-sized parameter set is rejected before any modular exponentiation runs on it                                                                                                                                                                                                                                                                                                                                                                |
| `PP-31` | `test_parameter_validation_fails_closed` parametrises four mutations — wrong `\|p\|`, `q ∤ p−1`, `g` out of range, `g` outside the subgroup — and asserts the exact message substring for each                                                                                                                                                                                                                                                                                        |
| `PP-53` | **The bit-length expectations come from `PROFILE_BIT_LENGTHS` in code, never from the artefact.** `load_profile()` looks the pair up by profile id — `EPD2-CRYPTO-1` is `(4096, 256)` — so checks 1 and 2 compare the loaded file against an expectation an attacker editing that file cannot reach                                                                                                                                                                                   |
| `PP-54` | **`load_profile()` runs further checks around the sequence above, and all of them fail closed.** For a JSON artefact, in order: the constants are canonical lower-case hex; the artefact's own `parameter_digest` recomputes from its constants; for the target, that digest equals the pinned `EPD2_CRYPTO_1_PARAMETER_DIGEST`; `p = q·r + 1`; and the artefact's `profile_id` matches the profile it was loaded as. Only then is the candidate handed to `validate_parameter_set()` |
| `PP-55` | **There is no cached-validation path and no fast path keyed on the profile name.** A caller that wants the target profile more than once holds the returned frozen object; it does not get a cheaper load. `testing/fixtures.target_params()` caches the _validated_ object for the test suite, which skips repeating a check rather than skipping one                                                                                                                                |
| `PP-56` | Primality checking is **on by default** and is on for the target profile: `load_target_profile()` runs `is_probable_prime()` over both the 4096-bit `p` and the 256-bit `q` on every load that does not explicitly disable it                                                                                                                                                                                                                                                         |

### 3.1 Subgroup membership is a separate, always-on check

`is_in_subgroup(value, params)` requires `0 < value < p` **and**
`value^q ≡ 1 (mod p)`. `require_in_subgroup()` is its raising form.

| ID      | Rule                                                                                                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `PP-32` | Membership is checked on **every** ciphertext component, public key and proof element before any verification equation is evaluated. Range alone is not accepted as membership |
| `PP-33` | `test_subgroup_membership_rejects_zero_and_out_of_range` pins that `0`, `p` and `p + 1` are all rejected                                                                       |

### 3.2 The canonical form a parameter digest is taken over

`ParameterSet.canonical_bytes()` is an ordered `EPD2-ENC-1` struct of
exactly seven fields, in this order: `parameter_set_id`,
`profile_version`, `p_bit_length`, `q_bit_length`, `p`, `q`, `g`.
`digest()` is `h(ZERO_KEY, PARAMETER_SET, [canonical_bytes()])`, a full
32-byte HMAC-SHA-256 output.

| ID      | Rule                                                                                                                                                                                            |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-34` | `p` and `g` are encoded as group elements at the full `p_bytes` width; `q` as a scalar at the full `q_bytes` width. There is no short form, so two encoders cannot disagree about leading zeros |
| `PP-35` | The declared bit lengths are inside the digested struct, so a parameter set cannot be re-labelled with a different claimed size without changing its digest                                     |

## 4. `is_probable_prime()` is not a primality proof

The implementation is a small-factor sieve over the 54 primes below 256,
followed by Miller–Rabin using the first `rounds` of those primes as bases
(`rounds = 24` by default, so bases 2 through 89).

Its own docstring says so: _"Not a primality **proof**."_

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                         |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-36` | **This function establishes probable-primality only.** No document, test or vector in PACK-16D may describe its output as a proof of primality                                                                                                                                                                                                                               |
| `PP-37` | The bases are **fixed and publicly known**. That is fine for a value this round generated itself; it is not sufficient for a parameter set supplied by a third party, because a party that chooses the candidate can target a known base set — composites that are strong pseudoprimes to a prescribed set of bases are constructible                                        |
| `PP-38` | The correct answer for a production profile is a **primality certificate from the parameter publisher**, checked independently. This round has none, for any profile, including `EPD2-CRYPTO-1`: what it has is probable-primality of `p`, `q` and `r/2` computed here (`PP-06`), which is evidence about the transcription, not a certificate                               |
| `PP-39` | Probable-primality of `EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256`'s `p` is **not part of this round's pinned evidence**. `production_shaped_params()` in `testing/fixtures.py` and `test_p4096_profile_has_the_electionguard_small_prime` both load it with `check_primality=False`. The 1024/160 profile and **the target profile** are both loaded with primality checking on |

## 5. Limitations — stated, not softened

| ID      | Limitation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PP-40` | **`VO-08` remains OPEN.** PACK-16D does not close it. Its owner is the PACK-16B external cryptographic review with independent confirmation in PACK-17                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `PP-41` | **No BSI conformity is claimed** by this document, by `crypto/parameters.py`, or by any profile in it. Nothing here was assessed against a BSI Technische Richtlinie                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `PP-42` | **`load_profile()` takes the bit-length expectations from `PROFILE_BIT_LENGTHS`, a dict declared in `crypto/parameters.py`**, so checks `PP-20` and `PP-21` compare the loaded file against an expectation an attacker editing that file cannot reach. An earlier version passed `expect_p_bits=candidate.p.bit_length()`, which compared a value against itself and passed for any file. `test_verifier_branches.test_profile_bit_lengths_come_from_code_not_from_the_file` pins the declared pairs and that every registered profile has one. **The verifier now uses the same dict**: `verify_record` looks the record's `parameter_set_id` up in `PROFILE_BIT_LENGTHS`, returns `UNSUPPORTED_PROFILE` when there is no entry, and validates against the declared pair — so the tautological path recorded here previously is gone |
| `PP-43` | **No verifiable-generation evidence exists for either TEST profile.** Their `.params` files record `p`, `q` and `g` and nothing else — no seed, no counter, no generation transcript. A reader cannot re-derive them; they can only re-check the structural relations of §3. The target profile is in a different position: it carries a named authoritative specification, the structural relations of `PP-06`, and the offline reconstruction of §1.5 — which is closer to a generation transcript than anything either TEST profile has                                                                                                                                                                                                                                                                                            |
| `PP-75` | **One provenance gap remains and it is not the commit pin.** The specification digest recorded in the artefact was inherited from PACK-16B and has not been re-verified since (`PP-61`); the upstream file's digest was computed on a network-enabled host rather than in the build session (`PP-70`). Both are gaps in who has checked _what_, not in what is recorded, and neither is closed by the arithmetic — what the arithmetic does is make the parameter values independent of both                                                                                                                                                                                                                                                                                                                                          |
| `PP-44` | **`validate_parameter_set()` still has no cofactor-structure check.** The `r/2`-prime property is checked for the target profile in `test_epd2_crypto_1_structural_provenance`, and `p = q·r + 1` is checked in `load_profile()` for a JSON artefact (`PP-54`) — but the general validator does not enforce either, and `ParameterSet.cofactor` is exposed without being validated there                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `PP-45` | **Nothing here is constant-time.** `pow(a, b, m)` and Python's arbitrary-precision `int` offer no side-channel guarantee, and none is claimed. This is `OD-P16D-05` and it is a production blocker, not a note                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `PP-46` | **`profile_version` is read from the artefact**, defaulting to `"EPD2-PARAM-1"` when the artefact does not declare one; `EPD2-CRYPTO-1.json` declares `"EPD2-PARAM-2"`. It is inside the digested canonical struct (`PP-35`), so a re-labelled profile version changes the parameter-set digest                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `PP-47` | Interoperability with ElectionGuard or any other implementation is **unestablished** (`OD-P16D-02`). The parameters are named against a published specification and cross-checked on `EPD2-CRYPTO-1` itself by an independent Node.js oracle, which narrows the question but does not settle it: no comparison against another _complete_ ElectionGuard implementation exists. Sharing a value of `q` is not interoperability                                                                                                                                                                                                                                                                                                                                                                                                         |

### 5.1 Measured cost of the real profile

Benchmark figures, not capacity figures, and no validation was disabled to
obtain them:

```text
parameter validation (incl. primality)      3.984 s
single selection encryption                 0.014 s
selection proof generation                  0.076 s
selection proof verification                0.205 s
ballot encryption (1 contest, 3 slots)      0.529 s
ballot proof verification                   0.889 s
3-of-5 ceremony (DKG)                       1.847 s
ceremony verification                       0.254 s
3 threshold shares + proofs                 0.189 s
3-of-5 tally verification + combination     0.641 s
peak RSS                                   18.8 MB
```

The `EPD2-CRYPTO-1` suite is now **25 tests in 28.12 s**
(`test_epd2_crypto_1.py`). Separately, the target-profile
cross-implementation suite is 15 tests in 8.06 s
(`test_target_conformance.py`, marked `slow_conformance`), and its
per-operation timings are exported next to its fixtures rather than
transcribed here.

The four-second validation is the reason `testing/fixtures.target_params()`
caches the validated object (`PP-55`), and the reason the fast test profile
still exists for the property and concurrency suites.

## 6. What this document does not decide

```text
BSI conformity / VO-08                     → PACK-16B external review, PACK-17
Primality certificates for any profile     → PACK-17
Re-fetching the pinned upstream file's
  bytes in this build session              → one `curl | sha256sum`; the pin
                                             and digest are recorded (PP-70)
Constant-time bignum arithmetic            → OD-P16D-05, production hardening
Production key ceremony and custody        → PACK-16B, OD-P16D-11, not implemented here
Interoperability / a second complete
  implementation                           → OD-P16D-02, PACK-17
Which profile a real election may use      → GOVERNANCE; none may today
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
