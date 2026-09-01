# PACK-16D — Randomness Implementation

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Two sources that cannot be confused

`services/voting-service/src/epd2_voting_service/reference/crypto/randomness.py`
defines exactly two sources and one factory. Cryptographic code depends
only on the `RandomSource` Protocol, whose surface is three members:
`is_deterministic`, `random_bytes(count)` and `random_below(bound)`.

| ID      | Rule                                                                                                                                                                                       |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `RN-01` | **`ProductionRandomSource` draws from the OS CSPRNG and fails closed.** It has no seed parameter at all, so no caller can make it deterministic even by accident                           |
| `RN-02` | **`DeterministicTestRandomSource` is seeded and reproducible, and refuses to construct unless the process is explicitly in a test profile.** Two independent guards, described in §3       |
| `RN-03` | `is_deterministic` is a class attribute on both — `False` on the production source, `True` on the test source — so the distinction is observable at runtime and is not a naming convention |

## 2. The production source

```text
ProductionRandomSource.random_bytes(count)
    count <= 0                     -> ValueError
    secrets.token_bytes(count)     -> any exception becomes RandomnessUnavailableError
    short read                     -> RandomnessUnavailableError
```

| ID      | Rule                                                                                                                                                                                                       |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-04` | The source is `secrets.token_bytes`, the Python standard library's OS CSPRNG interface. **No cryptographic dependency was added to obtain randomness**                                                     |
| `RN-05` | **No seed. No reseed hook. No fallback.** There is no software PRNG behind the OS CSPRNG, so there is nothing to degrade to                                                                                |
| `RN-06` | Any failure raises `RandomnessUnavailableError`, whose `reason_code` is `CRYPTO_RANDOMNESS_UNAVAILABLE`. A voting operation that cannot obtain entropy **fails**; it does not proceed with weaker material |
| `RN-07` | A short read is treated as a failure in its own right, not silently retried or padded                                                                                                                      |
| `RN-08` | The exception is raised `from exc`, so the underlying cause stays in the traceback for an operator while the reason code stays stable for the caller                                                       |

## 3. The deterministic test source and its two guards

Construction requires **both** of the following. Either one alone raises
`DeterministicSourceForbiddenError` (`reason_code =
"CRYPTO_TEST_MODE_REACHABLE"`):

| #   | Guard                                                     | Failure                                                                         |
| --- | --------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 1   | `allow_in_test=True` passed explicitly at construction    | `"DeterministicTestRandomSource requires allow_in_test=True"`                   |
| 2   | Environment marker `EPD2_VOTING_REFERENCE_TEST_PROFILE=1` | `"DeterministicTestRandomSource requires EPD2_VOTING_REFERENCE_TEST_PROFILE=1"` |

| ID      | Rule                                                                                                                                                                                                                                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-09` | **Two guards of different kinds, deliberately.** One lives in the call, the other in the process environment. A stray keyword argument in code is not sufficient, and a stray environment variable on a host is not sufficient. An accident has to happen twice, in two different places, to reach a deterministic source |
| `RN-10` | `allow_in_test` defaults to `False`, so the plain construction `DeterministicTestRandomSource(seed)` is always refused                                                                                                                                                                                                    |
| `RN-11` | An empty seed raises `ValueError`. There is no default seed                                                                                                                                                                                                                                                               |
| `RN-12` | Both guards are evaluated at **construction time** only. An instance that already exists keeps working if the environment marker is later removed. This is a real property of the design and not a defect, but a reader should know it                                                                                    |

## 4. `select_source()` provably cannot return a deterministic source

```python
def select_source(profile: str) -> RandomSource:
    if profile != "production":
        raise DeterministicSourceForbiddenError(...)
    return ProductionRandomSource()
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-13` | **`select_source` is the only factory production code calls.**                                                                                                                                                                                                                                                                                                      |
| `RN-14` | It accepts **only** the literal string `"production"`. The comparison is exact: `"PRODUCTION"`, `"Production"`, `"test"`, `"deterministic"`, `"debug"` and `""` all raise. There is no normalisation step, no case folding and no prefix matching, because each of those is a place where an unintended string could be accepted                                    |
| `RN-15` | **The function body contains exactly one `return`, and it constructs a `ProductionRandomSource`.** There is no branch, no table, no registry and no configuration lookup that could produce a different type. The claim "`select_source` cannot return a deterministic source" is therefore a property of the control flow, not a promise about how it will be used |
| `RN-16` | This is asserted by test, not by convention: `test_select_source_can_never_return_a_deterministic_source` in `tests/reference/test_crypto_units.py` checks `select_source("production").is_deterministic is False` and then asserts that `"test"`, `"deterministic"`, `"debug"`, `""` and `"PRODUCTION"` each raise `DeterministicSourceForbiddenError`             |

## 5. `random_below` uses rejection sampling, and why

`ProductionRandomSource.random_below(bound)` does **not** call
`secrets.randbelow`. It draws whole bytes through its own `random_bytes`
and rejects:

```text
width     = ceil(bit_length(bound) / 8)
limit     = (256**width // bound) * bound
repeat:
    candidate = int.from_bytes(random_bytes(width), "big")
    if candidate < limit: return candidate % bound
```

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-17` | **The reason is the failure path, not the distribution.** `secrets.randbelow` reaches the OS CSPRNG through its own internal route; when that route fails, the caller sees a bare `OSError` from deep inside the standard library. Routing every draw through `random_bytes` means a CSPRNG failure surfaces as `RandomnessUnavailableError` with `reason_code = CRYPTO_RANDOMNESS_UNAVAILABLE`, through the same fail-closed path as every other randomness failure |
| `RN-18` | An `OSError` escaping into ballot encryption is an untyped failure with no reason code. It would be caught, if at all, by a generic handler that cannot tell entropy exhaustion from a file-system error. **The whole point of a fail-closed reason code is that it is specific**, and that requires one entry point                                                                                                                                                 |
| `RN-19` | Candidates at or above `limit` are discarded and redrawn, so the result is uniform over `[0, bound)` rather than modulo-biased. `limit` is the largest multiple of `bound` that fits in `width` bytes                                                                                                                                                                                                                                                                |
| `RN-20` | The loop is unbounded by construction. It terminates with probability 1; the acceptance probability follows from `limit = floor(256^width / bound) · bound` and is above one half for every `bound`, so the expected number of draws is small. **This is an analytic remark about the two lines above; it is not a measured figure and no test measures it**                                                                                                         |
| `RN-21` | `bound <= 0` raises `ValueError` before any entropy is drawn                                                                                                                                                                                                                                                                                                                                                                                                         |
| `RN-22` | All nonce and blinding-factor generation in the reference goes through this method as `1 + source.random_below(q - 1)`, giving a uniform non-zero scalar in `[1, q-1]` — `elgamal.random_nonce`, the three scalars each branch of the disjunctive selection proof draws, the contest-sum commitment and the decryption-share commitment                                                                                                                              |

### 5.1 The test that pins it

`test_production_random_source_reports_failure_rather_than_degrading` in
`tests/reference/test_verifier_branches.py` monkeypatches
`randomness.secrets.token_bytes` to raise `OSError("entropy pool
unavailable")` and then asserts that **both**

- `source.random_bytes(32)` and
- `source.random_below(97)`

raise `RandomnessUnavailableError`.

| ID      | Rule                                                                                                                                                                                                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `RN-23` | The second assertion is the one that matters. It only passes because `random_below` goes through `random_bytes`; with `secrets.randbelow` it would raise `OSError` and the test would fail. **The rejection-sampling change is pinned by a test that fails if it is reverted** |
| `RN-24` | `test_production_random_source_rejects_non_positive_bounds` pins `RN-21` and the `count <= 0` guard                                                                                                                                                                            |

## 6. Every test in force

| Test                                                                  | File                        | Pins                                                                                                                                                                                                                                    |
| --------------------------------------------------------------------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_production_source_is_never_deterministic`                       | `test_crypto_units.py`      | `is_deterministic is False`; 16 bytes returned; two successive draws differ                                                                                                                                                             |
| `test_select_source_can_never_return_a_deterministic_source`          | `test_crypto_units.py`      | `RN-14`, `RN-15`, `RN-16`                                                                                                                                                                                                               |
| `test_deterministic_source_requires_both_guards`                      | `test_crypto_units.py`      | `RN-09` — removes the environment marker and asserts the `allow_in_test=True` call still raises, then sets the marker and asserts the call without the keyword raises. Both halves are checked, so neither guard can be quietly dropped |
| `test_deterministic_source_is_reproducible`                           | `test_crypto_units.py`      | Same seed gives the same 64 bytes; a different seed does not                                                                                                                                                                            |
| `test_production_random_source_reports_failure_rather_than_degrading` | `test_verifier_branches.py` | `RN-06`, `RN-17`, `RN-23`                                                                                                                                                                                                               |
| `test_production_random_source_rejects_non_positive_bounds`           | `test_verifier_branches.py` | `RN-21`                                                                                                                                                                                                                                 |

| ID      | Rule                                                                                                                                                                                    |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-25` | `test_deterministic_source_requires_both_guards` saves and restores the environment marker in a `finally` block, so it cannot leave the process in test profile and weaken a later test |

## 7. Limitations — stated, not softened

| ID      | Limitation                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-26` | **`DeterministicTestRandomSource.random_below` is modulo-biased on purpose.** It draws `ceil(bits/8) + 8` bytes and reduces modulo `bound`, with no rejection loop. The eight extra bytes make the bias negligible but not zero. This source is test-only and is never reachable from `select_source`; the property is recorded so nobody mistakes it for the production algorithm                               |
| `RN-27` | **The guards are runtime checks, not an import boundary.** Nothing prevents a module from importing `DeterministicTestRandomSource` directly; what stops it being _used_ is `RN-09`. No AST test asserts that production modules do not import it, although such a test exists for the verifier's import boundary                                                                                                |
| `RN-28` | **Inside the test suite both guards are satisfied globally.** `testing/fixtures.enable_test_profile()` sets `EPD2_VOTING_REFERENCE_TEST_PROFILE=1` in the process environment, so once any fixture has run, guard 2 is satisfied for the rest of that process. That is what makes the deterministic source usable in tests at all, and it means the two-guard property is only meaningful outside a test process |
| `RN-29` | **`random_bytes` catches `Exception`, not only `OSError`.** A programming error inside the call would also be reported as `CRYPTO_RANDOMNESS_UNAVAILABLE`. Fail-closed is preserved; diagnostic precision is not                                                                                                                                                                                                 |
| `RN-30` | **The quality of the OS CSPRNG is assumed, not verified.** There is no entropy-health check, no startup self-test and no continuous test on the output, all of which a production deployment on a hardware source would need                                                                                                                                                                                     |
| `RN-31` | **No secret material is zeroized.** Nonces and seeds are Python `int` and `bytes` objects; Python cannot reliably zeroize them and the garbage collector may have copied them. This is stated as a limitation, not solved                                                                                                                                                                                        |
| `RN-32` | **There is no nonce-reuse detector.** Each selection draws a fresh nonce, and a proof is bound to its context so a copied proof does not transfer, but a caller that supplies the same nonce twice is not caught by anything in this module                                                                                                                                                                      |
| `RN-33` | **No constant-time behaviour is claimed** for any operation that consumes this randomness (`OD-P16D-05`)                                                                                                                                                                                                                                                                                                         |
| `RN-34` | The property tests that exercise this module are **deterministic randomised loops** over a seeded source, 40 cases each, not `hypothesis` strategies — `hypothesis` could not be installed (PyPI HTTP 403). They do not shrink counterexamples and do not search adversarially (`OD-P16D-03`)                                                                                                                    |

## 8. What this document does not decide

```text
Production entropy source and health checks → PACK-17, production hardening
HSM-backed randomness                       → PACK-16B key custody, not implemented
Zeroization of secret material              → RN-31; unsolved, not deferred to a design
Static import boundary for the test source  → RN-27; unfinished
Hypothesis-based property search            → OD-P16D-03, PACK-17
Constant-time consumption of randomness     → OD-P16D-05
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
