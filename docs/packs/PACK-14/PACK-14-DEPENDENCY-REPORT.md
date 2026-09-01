**Round:** PACK-14 — implementation candidate. **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Repository version:** `0.14.0` · **Canon version:** unchanged at `0.8.0`

> **Superseding status note, added by the PACK-14 FINAL PASS round
> (2026-07-30).** The header above records the implementation-candidate
> round that wrote this document and is retained unchanged as the
> historical record. External GitHub Actions has since run against this
> exact tree and **passed every stage**, so PACK-14 is now **FINAL PASS**
> at `REPOSITORY_VERSION 0.14.0` / `CANON_VERSION 0.8.0`. The PASS changes
> the _round's_ status and nothing else: no limitation below is closed by
> it, and **NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.** See
> `docs/handover/PACK-14-FINAL-PASS-REPORT.md` and
> `docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md`.

# PACK-14 — Dependency Report

## 1. New third-party dependencies: none

This round adds **no** Python or Node dependency. `pyproject.toml`'s
dependency groups, `uv.lock` and `package-lock.json` are unchanged, which
is why the CI step "Fail if lock files were modified by install" is
unaffected.

That is a deliberate consequence of the port design rather than a
coincidence: every operation that would have required a library — WebAuthn
verification, password hashing, TOTP, assertion signature verification —
is a `Protocol` whose default binding **refuses**, and the bound
alternatives in the test suite are explicit test doubles that name
themselves as such.

The correction round's reference persistence path and runnable service
boundary hold to the same rule. Persistence uses **`sqlite3` from the
Python standard library**, so a real migration runner, real DDL and real
durable adapters cost no dependency. The service boundary is a
**transport-agnostic** request/response adapter rather than a web
framework: `ApiRequest` and `ApiResponse` are dataclasses, and binding
them to HTTP is a deployment's job, along with the framework that would
require.

## 2. The four unmet bindings

| Port                         | Default binding                               | What a deployment must bind                                 |
| ---------------------------- | --------------------------------------------- | ----------------------------------------------------------- |
| `WebAuthnVerifier`           | `UnboundWebAuthnVerifier` — refuses           | A mature, audited WebAuthn library                          |
| `PasswordHasher`             | `UnavailablePasswordHasher` — refuses         | Argon2id or scrypt with governed parameters                 |
| `BreachedPasswordChecker`    | `UnboundBreachedPasswordChecker` — refuses    | A breached-password corpus or service                       |
| `AssertionSignatureVerifier` | `UnboundAssertionSignatureVerifier` — refuses | The provider's own library, or a mature JOSE implementation |

**All four refuse.** An earlier draft of this round shipped a
`NoBreachedPasswordChecker` that reported nothing as breached; it has
been removed. That default was wrong in the direction a security default
must never be wrong — a deployment that had not bound a checker would
have discovered the fact after a credential-stuffing incident rather than
at enrollment.

The replacement is `UnboundBreachedPasswordChecker.is_breached`, which
raises `BREACH_CHECK_UNAVAILABLE` rather than returning either boolean,
because both booleans are lies: `False` claims a check that did not
happen, and `True` would refuse every password for the wrong reason. So
**no checker means no password enrollment and no password replacement.**

One governed exception exists, and its shape is the point:
`PasswordDegradedModeDecision` lets a deployment decide, with a named
authority and a registered reason code, that a holder of an **already
stored** hash may still authenticate while no checker is bound. It has
exactly four fields and `allows_authentication` is the only boolean among
them — there is no field a caller could set to re-open enrollment. A test
asserts the field set, so adding one is a failing test rather than a code
review someone might wave through.

`tests/repository/test_pack14_default_binding.py` asserts that the
runtime composition root binds all four refusing adapters, and
`services/identity-service/tests/test_pack14_security.py` asserts that
the removed permissive class has not returned.

## 3. The test doubles, and why they are safe

| Double                                    | Used for                                      | Why it cannot leak into production                                                                              |
| ----------------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `DeterministicSecureRandom`               | Reproducible artifacts in tests               | A separate class; `SystemSecureRandom` has no test mode                                                         |
| `DeterministicWebAuthnVerifier`           | The ceremony state machine and its negatives  | A separate class; the production path has no branch                                                             |
| `DeterministicTotpVerifier`               | The factor lifecycle                          | Same                                                                                                            |
| `DeterministicAssertionSignatureVerifier` | The adapter's eight checks                    | Same                                                                                                            |
| `DeterministicBreachedPasswordChecker`    | Both branches of the enrollment breach check  | A separate class, named a test double in its docstring; the default is the refusing one                         |
| The `InMemory*` storage adapters          | Unit tests of domain rules without a database | Not the runtime binding — `runtime.build_identity_service` names none of them, and a repository test asserts it |

None of the four is reachable by setting a flag on a production adapter,
which is the failure mode the task's "no placeholder security behaviour"
rule exists to prevent.

## 4. Internal dependencies

`epd2_core` (event envelope, canonical JSON, clock, identifiers,
version) and `epd2_audit_core` (governed audit ingestion). Both are the
one-directional dependencies every service already has.

**No cross-service import was added.** In particular `identity-service`
does **not** import `account-service`, which is why canon 7.2's status
enum is deliberately duplicated and why
`tests/repository/test_pack14_duplicated_logic_parity.py` exists.

## 5. Cross-pack contracts consumed

| Pack     | What is used                                  | How                                                 |
| -------- | --------------------------------------------- | --------------------------------------------------- |
| PACK-09  | Retention schedules, legal hold               | `persistence.assert_disposition_permitted`          |
| PACK-11  | Evidence bundles                              | Held by reference; no content copied                |
| PACK-12  | JIT grants, break-glass, separation of duties | `administration.PrivilegedGrantRef`, a value object |
| PACK-13  | The canonical event envelope                  | Used unchanged                                      |
| FRONT-00 | The ten workspaces and their origins          | Mirrored server-side, parity-tested                 |
