# PACK-12 — Implementation Candidate Report

**PACK-12 IMPLEMENTATION CANDIDATE**

**LOCAL VERIFICATION INCOMPLETE / EXTERNAL CI PENDING / NOT FINAL PASS**

Section 5 enumerates each verification stage individually.

| | |
| --- | --- |
| Round | PACK-12 — Privileged Administration, Authorization-Aware Search & Governed Data Export |
| Date | 2026-07-29 |
| Baseline | `EPD2_PACK-11_GOVERNED_DOCUMENTS_EVIDENCE_0.11.0_FINAL_PASS.zip` |
| Repository version | `0.11.0` → **`0.12.0`** |
| Canon version | `0.8.0` — **unchanged** |
| Register entry | `FIR-ROADMAP-002` → `scheduled` (**not** `implemented`) |
| Files added | 56 |
| Files changed | 17 |
| Files removed | 0 |

---

## 1. What this round produced

One wholly new service, `services/privileged-access-service`, implementing
the PACK-12 specification as a reference implementation: 17 source modules
and 16 test modules, 327 tests of its own.

It carries three logical bounded contexts inside one package boundary,
one command frame and one audit path — the resolution of `OD-P12-04`.
They are one control surface: a privileged grant that could be reasoned
about without the search and the export it authorises is a control in
name only, and splitting them would have put the answer to that question
across three audit paths, which is exactly what `OD-P12-06` forbids.

| Context | Aggregates | Modules |
| --- | --- | --- |
| Privileged administration | `PrivilegedAccessGrant`, `BreakGlassActivation`, `PrivilegedSession` | `access`, `breakglass`, `sessions` |
| Authorization-aware search | `QueryAudit`, `IndexPolicy` | `search`, `classification` |
| Governed export, DLP, disclosure control | `ExportRequest`, `ExportArtifact`, `DlpAssessment`, `DisclosureRiskAssessment` | `export`, `dlp`, `disclosure` |

Alongside it: `contracts/reason-codes/pack-12.yml` (141 entries), the nine
PACK-12 specification documents, the eight proposed ADRs, and the merged
master register.

---

## 2. Open decisions closed this round

| Decision | Resolution | Where it lives in the code |
| --- | --- | --- |
| `OD-P12-02` — a separate investigative search mode? | **No.** Investigation is a *purpose* inside the ordinary scoped search. `SearchMode` has exactly two members and there is no third; `Purpose.INVESTIGATION` narrows like every other purpose and additionally requires an explicit grant. | `search.SearchMode`, `search.GRANT_REQUIRED_PURPOSES`, `domain.Purpose` |
| `OD-P12-03` — hard-coded limits or versioned policy? | **Versioned policy, with ceilings that configuration cannot raise.** Every limit is a field on `PrivilegedAccessPolicy`; `MAX_ALLOWED_GRANT_DURATION`, `MAX_ALLOWED_BREAK_GLASS_DURATION` and `MINIMUM_ALLOWED_COHORT_THRESHOLD` are module constants a policy file cannot exceed. The shipped numbers are **reference defaults, not legally approved policy**. | `policy.py`, `REFERENCE_POLICY` |
| `OD-P12-04` — one service or three? | **One package boundary, three contexts**, separated by module, aggregate and role rather than by deployable. | the package layout; `tests/repository/test_service_boundaries.py` |
| `OD-P12-06` — a new audit subsystem for query audit? | **No.** `QueryAudit` is a typed PACK-12 record appended to PACK-02's existing chain. PACK-12 gains no mutating control over `audit-core`: `storage.delete_privileged_record` exists only to refuse, because "we simply never call it" is not a control. Session evidence seals into PACK-11's bundles; retention stays PACK-09's. | `storage.QueryAudit`, `storage.delete_privileged_record`, `sessions.seal` |
| `OD-P12-07` — how to model external recipients? | **A closed taxonomy with no generic `external`.** Five categories, each with its own tier eligibility and channel eligibility. "External" is not a category an obligation can be attached to. | `export.RecipientCategory`, `_RECIPIENT_TIER_ELIGIBILITY` |
| `OD-P12-08` — how far does cumulative disclosure reach? | **A bounded model that fails closed.** A policy window, a policy limit, and a `ReleaseHistory` that must be *available*. An unbounded model was rejected as unimplementable, and an unimplementable model quietly becomes no model at all. | `disclosure.evaluate_cumulative`, `ReleaseHistory.assert_available` |

---

## 3. The guarantees that are structural rather than documented

Each of these is enforced by construction and covered by a test that
fails if the construction changes.

1. **No bypass.** No feature flag, environment switch, deployment mode,
   privileged grant or emergency path disables any invariant, audit
   append or separation check. Emergency access is a separate workflow
   that only *adds* obligations. (`roles.NO_BYPASS_NOTE`; `P12-BG-009`,
   FIR-INV-006.)
2. **No standing superuser is expressible.** `EffectiveWindow` has no
   "no end" option; there is no `renew` and no `extend`. (`P12-PAM-003`.)
3. **No universal console.** Holding every privileged role at once is
   refused by the incompatibility matrix; no role set reaches ballot
   content or mutates an audit record. (FIR-INV-014, FIR-INV-002.)
4. **PACK-08's incompatibility baseline is preserved and made stricter,
   never relaxed** — one preserved institutional pair plus fourteen
   additions, and the matrix is re-checked at the moment of the act
   against the roles the actor *really* holds. (Canon 19e.16.)
5. **Separation of duties is evaluated twice** — at approval and again at
   activation — because a subject's role set can change in between.
   (`P12-PAM-005`.)
6. **Audit before event.** `_finish` appends the audit row, then
   publishes, then records idempotency. An event that reached the stream
   without an audit row is an unaccountable act.
7. **No deletion.** No storage port defines a delete-shaped method, with
   one named exception — `SearchIndexStore.remove`, which requires
   `IndexRemovalEvidence` naming the PACK-09 or PACK-11 decision it
   followed. Removing a record from the index is not deleting the record.
8. **No voting reference type is declared**, so a caller cannot reach for
   one. (`P12-VOTE-001`.)
9. **Session evidence carries no secret.** `PROHIBITED_PAYLOAD_KEYS` is
   applied at seal time and again before every event is built; the
   summary type has no `payload`, `body`, `content` or `response` field
   for content to occupy. (`P12-SES-007`.)
10. **Export fields are selected, never stripped.** A row assembled whole
    and then filtered has existed whole, and what has existed whole can
    leak whole. (`P12-EXP-008`.)

---

## 4. Wording that was checked, not assumed

The following claims are **not** made anywhere in the added code, tests
or documentation, and each has a positive replacement:

| Not claimed | What is said instead |
| --- | --- |
| tamper-resistant | tamper-**evident** — alteration is detectable, not prevented |
| the copy was deleted / retrieved / recalled | revocation withdraws authorization and blocks further platform-mediated access |
| destroyed | a destruction **attestation** by the recipient — a statement, not a verified fact |
| the watermark prevents leakage | a watermark marks a copy; it does not stop one being made |
| production-ready | reference implementation; every adapter is in-memory |
| legally valid / admissible / compliant | a determination recorded with its own authority and reason code |

---

## 5. Verification — what ran, and what did not

**This section is the reason this artifact is a candidate.**

The build environment cannot reach the package registries:

```text
uv sync --all-groups --frozen  →  × Failed to download `sortedcontainers==2.4.0` … 403 Forbidden
npm ci                         →  npm error code E403
uv lock                        →  × An index URL (https://pypi.org/simple) could not be
                                    queried due to a lack of valid authentication
                                    credentials (403 Forbidden)
```

`make verify` therefore could not be run. Per the round's own rule, this
artifact is **not** labelled "local verification complete".

### 5.1 Stages that ran, with results

| Stage | Command actually run | Result |
| --- | --- | --- |
| Python lint | `ruff check .` | **PASS** — all checks passed, whole repository |
| Python format | `ruff format --check .` | **PASS** — 302 files already formatted |
| Python types | `mypy <each target from the Makefile>` | **PASS** — every target reports Success |
| Python tests | `pytest` (repository-wide) | **4053 passed, 5 skipped** |
| — of which PACK-12's own | `pytest services/privileged-access-service/tests` | **327 passed** |
| Reason-code registry | `pytest tests/contract/test_reason_codes_registry.py` | **44 passed** — every literal in the service is registered |
| Repository structure | `pytest tests/repository/` | **PASS** after this report is added |
| Lockfile structure | `python -m tomllib` parse + shape comparison | **PASS** — see 5.3 |

Tool versions used locally were resolved from a standalone install, not
from the project's locked dev group, because that group cannot be
installed here. A version-skew difference between these and CI's is
possible and is itself a reason the external run is required.

### 5.2 Stages that could NOT run

| Stage | Why | Consequence |
| --- | --- | --- |
| `uv sync --all-groups --frozen` | PyPI 403 | the project's own dev environment was never materialised |
| `uv lock` | PyPI 403 | see 5.3 |
| `npm ci` | npm registry 403 | no frontend stage below could run |
| `npm run format` / `format:check` (Prettier) | no `node_modules` | **markdown and JSON added this round are unformatted by Prettier and may fail `format:check` in CI** |
| `npm run lint` (eslint) | no `node_modules` | not run |
| `npm run typecheck` (`tsc`) | no `node_modules` | the TypeScript version test was edited but not executed |
| `vitest` | no `node_modules` | not run |
| Next.js build | no `node_modules` | not run |
| Playwright browser and visual tests | no browsers, no `node_modules` | not run |

**The Prettier row is the most likely first CI failure** and is called
out here so it is expected rather than surprising: this round adds
substantial Markdown (nine specification documents, eight ADRs, two
handover documents, a service README, ~660 register lines) and one large
YAML file, none of it passed through Prettier.

### 5.3 `uv.lock` — a hand-added entry, stated plainly

`pyproject.toml` now declares `epd2-privileged-access-service` as a
workspace member, a workspace source, a root dependency, a Ruff `src`
root, a first-party isort package, a mypy path and a pytest testpath. A
`uv.lock` that does not contain the member makes `uv sync --frozen` fail.

`uv lock` cannot run here. Rather than ship a lockfile that would
certainly fail, the entry was **added by hand**, following the exact
shape of the eighteen existing workspace entries:

- a `[[package]]` block placed in alphabetical position, with
  `source = { editable = "services/privileged-access-service" }` and the
  two workspace dependencies the service's `pyproject.toml` declares;
- one line in the root package's `[package.dependencies]`;
- one line in the root package's `[package.metadata].requires-dist`.

Verified structurally: the file parses as TOML, the new entry has exactly
the same key shape as `epd2-document-service`'s, and the root package
lists it in both places.

**Not verified:** that `uv` itself accepts it. `uv lock --check` fails
here for an unrelated reason (it cannot resolve `hypothesis` offline), so
it proves nothing either way. **CI must run `uv lock` and commit whatever
it produces.** If the hand-added entry differs from the generated one,
the generated one is correct.

### 5.4 What a PASS would require

1. `uv sync --all-groups --frozen` succeeding against a regenerated lock;
2. `make verify` green end to end on a networked runner;
3. `npm run format` applied to this round's Markdown and YAML;
4. the frontend stages (`tsc`, `vitest`, Next.js build, Playwright) green;
5. a separate FINAL PASS round that records the external CI evidence.

Until all five hold, `FIR-ROADMAP-002` stays at `scheduled`.

---

## 6. Deliberate exclusions

Not implemented, by instruction and by design: production database, real
event bus, external IAM/IdP, MFA, HSM/PKI, production search engine,
production DLP provider, voting of any kind, incident-response platform,
full frontend workspaces, real external recipient portal, legal
activation, production-readiness claims.

No second architecture, no second audit framework, no second evidence
system, no second reason-code registry, no second master register was
created.

`AC-P12-090` remains deferred. `AC-P12-019` is closed by the numeric
policy in `policy.py`.

See `docs/handover/PACK-12-KNOWN-LIMITATIONS.md` for the twelve named
limits in full.

---

## 7. Master register

`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` was updated
in place. **No second register was created.**

The user supplied an updated register mid-round. The merge took **the
existing repository file as the base** and appended only the genuinely
new material — sections 24 and 25, thirteen new entries (`FIR-UX-001`,
`FIR-UX-002`, `FIR-ID-001`, `FIR-ID-002`, `FIR-COMM-004`,
`FIR-SEARCH-001`..`003`, `FIR-SUPPORT-001`..`003`, `FIR-METRIC-001`,
`FIR-METRIC-002`).

That direction was deliberate and is worth recording: the supplied file
was derived from a **pre-PACK-11** baseline, so adopting it wholesale
would have silently reverted the PACK-11 round record, PACK-11's status
changes, its evidence paths and the current baseline pointer. The FIR
inventory confirms the merge lost nothing: 103 entries before, 116 after,
and every pre-existing identifier still present.

Also added this round: the PACK-12 round record (§1.6), the rewritten
`FIR-ROADMAP-002` entry, and "PACK-12 foundation provided — this entry is
NOT implemented" notes on the six entries PACK-12 touches.

---

## 8. Files added (56)

| File | SHA-256 |
| ---- | ------- |
| `contracts/reason-codes/pack-12.yml` | `bc0b003564ecb5290642095bbbb2a83e283eab3f3d2840dde24678e168855350` |
| `docs/adr/ADR-061-pack-12-privileged-role-separation.md` | `f6e80fa7356a3d5b40b0f9492c45df34eaaa5f400d1a9c3753a89dcbec69e178` |
| `docs/adr/ADR-062-pack-12-purpose-scoped-pam.md` | `6a7eda052d9aaa63d78a8d6024763decd68670d727654998a752aa4a629d861b` |
| `docs/adr/ADR-063-pack-12-break-glass-dual-control.md` | `1b3763eb1eed5f2306341cdaf1354555113fa3385bc32596360c0828e86edf02` |
| `docs/adr/ADR-064-pack-12-authorization-aware-search.md` | `749eb0cc3c82d8df218e7d71d87d2722aad2f5f641da27e6c7d8717adf5f3c75` |
| `docs/adr/ADR-065-pack-12-high-confidentiality-index-exclusion.md` | `7f61b45386de76a39bb4bae7fbc6da0c04903ac543edb0dfc0f799c6a3b4d30c` |
| `docs/adr/ADR-066-pack-12-governed-data-export.md` | `1d83682581b5c208baf1af01c21ec8d94f0b131d48d1f247cca1e41af027f0df` |
| `docs/adr/ADR-067-pack-12-dlp-and-disclosure-control.md` | `8ee5f2831d98661e2fd75b87412f9d43f9840f39d938fe153c3d8e8ccca17065` |
| `docs/adr/ADR-068-pack-12-privileged-session-evidence.md` | `7d63267013980701ed1aa1bf892f4239ab5767133c1b0fbb277f275414af3d58` |
| `docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md` | *self-referential — a file cannot contain its own digest; compute it from the delivered archive* |
| `docs/handover/PACK-12-KNOWN-LIMITATIONS.md` | `e2494d23074b41a5b02bbff692576b2772a57851763af66edd933c6d6d917c82` |
| `docs/handover/PACK-12-SPEC-ADR-REPORT.md` | `c467360c24e47e2490304698f2450b5af452b88ecf4eb0a5030d40be4044248e` |
| `docs/packs/PACK-12/PACK-12-ACCEPTANCE-MATRIX.md` | `4e57e65fb6ab90d281822a886b1e342783b41361f3d1a2633e0c9665f9ac7f15` |
| `docs/packs/PACK-12/PACK-12-CANON-ASSESSMENT.md` | `7f198c4f2593ba53a974432c5002dbf5dd93cb663a873dd179a73ae26fa062dc` |
| `docs/packs/PACK-12/PACK-12-DATA-SEARCH-EXPORT-MATRIX.md` | `bbe09c810077dd2d6f46db731354fb2e15b653f18946c3639a086d05f45bacb5` |
| `docs/packs/PACK-12/PACK-12-EVENT-CATALOG.md` | `20c2892720a99347b56f9d0f3b43ca71d63ddc44dcfa9daf0c319bcfe498d4bb` |
| `docs/packs/PACK-12/PACK-12-FIR-COVERAGE-MATRIX.md` | `5983cdcabcc42e2f1a17720235b81bb3de591dbd87179542179000d06c4209d4` |
| `docs/packs/PACK-12/PACK-12-REASON-CODE-CATALOG.md` | `d0c1ba673c435d44b562f4c12f37d12852e008035bea9514fc5e4656bd3927e8` |
| `docs/packs/PACK-12/PACK-12-ROLE-SEPARATION-MATRIX.md` | `8497dbd95e313f7347fd09af654034cc21cacfc5a6cda7dea6e4453c1e54b366` |
| `docs/packs/PACK-12/PACK-12-SPECIFICATION.md` | `0856e10ee108c94921203970705af14b8990ae3408ea1ffa1c93ed68b8af11c9` |
| `docs/packs/PACK-12/PACK-12-THREAT-MODEL.md` | `4f930b9af16e3b8ecc4498391f5eb8cdcd67e157468b7403bb705e2f6181a90c` |
| `services/privileged-access-service/README.md` | `b858bce28ce2f4b30577b22b3ccc78ccacd0f9fb2b1f219359c991376d664da8` |
| `services/privileged-access-service/pyproject.toml` | `d5af31e116f1c8bb2e4fbdf3fd33084ff9ed49bce53d3c23f64b57c2b1a6f2d5` |
| `services/privileged-access-service/src/epd2_privileged_access_service/__init__.py` | `0c2e766fd073f5c8e3ab75a90517d263e97e7ca3ce4fe7680380caaa31a3130e` |
| `services/privileged-access-service/src/epd2_privileged_access_service/access.py` | `ae7de8b509f29d85c4b6c17c888400a182efad62d801b3b4f246bd4ec3c8a419` |
| `services/privileged-access-service/src/epd2_privileged_access_service/application.py` | `fc4ffe6fa3ace444412b4776ea38d9b809ce7eee969eab8a7b4dc08db5b3f687` |
| `services/privileged-access-service/src/epd2_privileged_access_service/breakglass.py` | `ed53c20d881f39628c56d4e4ddb85bfe138462408db90b1c5dfdf23112cb11cf` |
| `services/privileged-access-service/src/epd2_privileged_access_service/classification.py` | `2a7228110f73337c9b203a1250c50302cc085adcac20c23c271ecf5224875ad2` |
| `services/privileged-access-service/src/epd2_privileged_access_service/disclosure.py` | `e5eb315851358302c23772d6a79f7a63619d7aa31b63b550bf7f0e7a401fa5df` |
| `services/privileged-access-service/src/epd2_privileged_access_service/dlp.py` | `3219910875d11ef9fc25ac3f85104a7b66ded48195b6b055873c89d66c467f7b` |
| `services/privileged-access-service/src/epd2_privileged_access_service/domain.py` | `fa5777735188f550a1771ec68ef5ab3c7163debcb577fdc20f93c90a69d8b4de` |
| `services/privileged-access-service/src/epd2_privileged_access_service/events.py` | `cbe6e5f6234bd71c9eb50e45cc72c0d809fc6eb5da60176b18a3e14354882bd3` |
| `services/privileged-access-service/src/epd2_privileged_access_service/exceptions.py` | `e6204d1cc9ff7523172ae57b28401353a23daedb20cbf2b5d7493daf91bd1dce` |
| `services/privileged-access-service/src/epd2_privileged_access_service/export.py` | `754805f0434f54e6a88ef9042207d712158180b62fbc2084bcba73a75b356b0a` |
| `services/privileged-access-service/src/epd2_privileged_access_service/policy.py` | `e31461cdd4565a9ea97add8366b8f526704c79b2543893db81bce14de6189fd4` |
| `services/privileged-access-service/src/epd2_privileged_access_service/references.py` | `932e2fa7f13e7521d0e29989e2794b28be640e05a5d1a81889f4d61c3388efaa` |
| `services/privileged-access-service/src/epd2_privileged_access_service/roles.py` | `73121629b282ccd40389ab32b7974668f5a5b0291310519087b4938b96ba8fcf` |
| `services/privileged-access-service/src/epd2_privileged_access_service/search.py` | `62887810fd4c6625e49e21274351843811cd16c60d93b05267c459804525811d` |
| `services/privileged-access-service/src/epd2_privileged_access_service/sessions.py` | `8e3833074ceedd39ff853be365bd2aa3cbb95d625412309be70ba02a0342a5e0` |
| `services/privileged-access-service/src/epd2_privileged_access_service/storage.py` | `742fe84928b85261145c50f9204a14871b0985b063a39d7369ac6f5267b445e0` |
| `services/privileged-access-service/tests/_privileged_builders.py` | `9e2fa8193c782aaaf042e91b10366d025254e99f53795e6c7a6cedfb0855fb6b` |
| `services/privileged-access-service/tests/conftest.py` | `9a627709e2c7f97ee468fd642acdd143df9666835dae7e9b1ed1dddb8f94765a` |
| `services/privileged-access-service/tests/test_access.py` | `fc8cc834f873cb21957d7f536d62260bd3debba48e0b7f4a6770b61ab186e21a` |
| `services/privileged-access-service/tests/test_application.py` | `570bbee233e42e8441a9b1fe3288ee26a7f3f109de678ead198e7a3a42ea6a8b` |
| `services/privileged-access-service/tests/test_application_flows.py` | `542507822f7bdf100fdf1e660847927c417a37a7d9a74252592baff5c1f984bd` |
| `services/privileged-access-service/tests/test_breakglass.py` | `f1b63bdbb515f0c463adbc75438123d641b8cd04d0a95eae9f53955a4bf1d1eb` |
| `services/privileged-access-service/tests/test_disclosure.py` | `28a9af4b45c1eb3542ca516a0181860ed771664b249abfa61e4d8de1ec0094f5` |
| `services/privileged-access-service/tests/test_dlp.py` | `49f01d8a0aa49594d60a9cacc6c3f83d976e7fcc62cc7b4e5c3398703470ff08` |
| `services/privileged-access-service/tests/test_domain.py` | `6d488b89c72c65fbe0041f83ea4fa0627a7205cbe895ce194af603c0ac0f1ce0` |
| `services/privileged-access-service/tests/test_events.py` | `f516c0e739ca156668d4d1043007cdb55c9c4c6818607263b06591d6759f68ca` |
| `services/privileged-access-service/tests/test_export.py` | `fdf9719c7f3cfac667246e070f08e2e9cd998fa48de8b0eeb80a75c23894df0c` |
| `services/privileged-access-service/tests/test_policy.py` | `d0c9946c2060ff2a70a671ec4f7d1e0e43ad47c14b0e27bc45ddbd8e618cf12f` |
| `services/privileged-access-service/tests/test_roles.py` | `d4b0c261707e9fd0977e9d0a17dac484baf7264a3a26549e90363a40732a9600` |
| `services/privileged-access-service/tests/test_search.py` | `9ec5e2351e7106dd45c14b3e478dbd42b827b303bd84518da01e8471438b4924` |
| `services/privileged-access-service/tests/test_sessions.py` | `2fb64a3b2fc4d7ff33e245726b6b9d0de3351396469e77fbe1eabf07e3422297` |
| `services/privileged-access-service/tests/test_storage.py` | `aca841e4cbcf37e684e77bc06c052e34d28dc6bff8c954c1bda143557543874a` |

---

## 9. Files changed (17)

| File | SHA-256 |
| ---- | ------- |
| `CHANGELOG.md` | `d7609a6cc407459c7e39414eefdf66dcaa3f26e6801f550c1a3da0f3d4113f48` |
| `Makefile` | `687a353a208619d64021d01d7fe49ab3263cfdcc5b4626bb053aedfe6d699e2f` |
| `README.md` | `23b0d7395ceb6119de7f0a55febd66abd4866475d0f2f98242adc03e16901b56` |
| `docs/adr/README.md` | `d2352d303d5811992019b6d2ca5316f4f550f0bd2fea41437dbff0ca6230fe93` |
| `docs/canonical/canon-version.json` | `8f57cb94e87c0fab2f5b95d69c7075451a3cca4b66b93183db02c092a07b8707` |
| `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` | `390e0513ff2497a9eb6c3a0fef4ff86fe5daafefc7407be3f865b2061fba828b` |
| `packages/python/epd2-core/src/epd2_core/version.py` | `8b78b9c405a4b0dcb4edcfd6ec554acdd2ebe5eeeaee5903a1900188d5574c78` |
| `packages/python/epd2-core/tests/test_version.py` | `29aca2274eace5904ad459e1da3aabe2607567052c93d7a450aeb5195033f227` |
| `packages/typescript/epd2-types/src/version.ts` | `2b10ff85c05ebe3fd8ad0b0ab32c94dc296f162bc7138d8185e1d53b7fd880d8` |
| `packages/typescript/epd2-types/tests/version.test.ts` | `70ce071eec4a4562655fcc3e3b621de5dabde59d5696216be5afe007ec87347e` |
| `pyproject.toml` | `f08883516b64b754b3f3e20671c45fac38d54b99c8f318b297278142e33478bf` |
| `scripts/check_canon_0_8_0.py` | `f1caae6504cfe1ed857b0b23a43bbe64fab087c2d3413c2c6945ea8ae5635fc6` |
| `scripts/check_repository.py` | `d07cfe9663e6d553f8bfdaa2aff23e35b389cbd39d48dced5f88beabca489d21` |
| `tests/contract/_schema_helpers.py` | `abeebddba99bad1d01cec125792fcfa9306669b4ea30c1948374293556e1af59` |
| `tests/contract/test_reason_codes_registry.py` | `fb79c6cd35aedabd9ba4e754c1c4cd758df004f2d23de6d8bd11da10598d586a` |
| `tests/repository/test_service_boundaries.py` | `3471fc5800d5ce3f16e9548f4156995670b588549003c98b24a9917d2199bfde` |
| `uv.lock` | `8777af7301103e56da94100891d57a6af3ac1a13a382272d74d027faf9ea61e8` |

---

## 10. Files removed

None.

---

## 11. Archive digest

The SHA-256 of the delivered archive is reported in the delivery message
accompanying it. It is deliberately not printed here: a file cannot
contain the digest of the archive that contains it, and a value that
looked authoritative but could not be true would be worse than an
honest pointer.

To verify:

```bash
sha256sum EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_CANDIDATE.zip
```

---

## 12. Correction round — 2026-07-29

A narrow documentation correction was applied after the first candidate
archive. **No implementation logic, test, scope, version, canon, CI
configuration or dependency was changed**, and `uv.lock` was not
regenerated or touched. Fifteen Markdown files changed; nothing was added
or removed.

What was wrong, and what it now says:

| Correction | Before | After |
| --- | --- | --- |
| Register, `FIR-ROADMAP-002` | "this round produced a **locally verified** reference implementation" | full local verification is **incomplete**, external CI is **pending**, with the stages that ran and did not run named |
| Register, inventory | "16 source modules, 12 test modules" | **17 source modules, 16 test modules, 327 tests** — the true counts |
| `CHANGELOG.md`, inventory | same wrong counts | corrected, plus the `uv.lock` hand-edit disclosure |
| Root `README.md` | headline version stale; no PACK-12 section | current status banner at `0.12.0`, a PACK-12 candidate section with the verification status, and PACK-11 explicitly kept as the historical FINAL PASS baseline |
| Nine PACK-12 specification documents and the spec/ADR report | "Specification-only. No code. Not implemented." — true of the specification round, misleading once the code exists | the original statement is preserved as the historical record, with a superseding status note pointing here |
| This report's banner and the service README | ad-hoc wording | the single label **LOCAL VERIFICATION INCOMPLETE / EXTERNAL CI PENDING / NOT FINAL PASS** |
| Sections 8 and 9 above | digests taken before the corrections | regenerated against the corrected tree |

The `uv.lock` disclosure in section 5.3 is unchanged and still stands:
the workspace-member entry was added by hand, is verified structurally
only, and **has never been accepted by `uv`**. It was deliberately not
regenerated, because no working resolver is available here and a
regenerated-looking lock that nothing validated would be worse than an
honest one that is labelled.

Delivered as
`EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_CANDIDATE_CORRECTED.zip`.
