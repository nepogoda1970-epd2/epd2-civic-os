# PACK-12 Privileged Administration, Search & Governed Export 0.12.0 — Final PASS Report

Status: **PACK-12 PRIVILEGED ADMIN, SEARCH & EXPORT 0.12.0 — FINAL PASS.**

```text
PACK-12 FINAL PASS
EXTERNAL GITHUB ACTIONS PASS
REPOSITORY_VERSION 0.12.0
CANON_VERSION 0.8.0
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

This is a **packaging round**. No implementation was rebuilt. No
`privileged-access-service` module was changed, no test was changed, no
reason code, ADR, contract, frontend file, route or visual snapshot was
touched, and neither the repository nor the canon version moved. The
archive is the externally verified tree plus the final status and handover
documents that close the round.

The PASS status rests on an **external GitHub Actions run**, not on
anything this environment could execute. Section 9 states exactly which
checks were re-run locally after the documentation edits and which are
accepted from that run; nothing network-dependent is claimed as locally
verified.

---

## 1. Input baseline — PACK-11

|                             |                                                                  |
| --------------------------- | ---------------------------------------------------------------- |
| Baseline archive            | `EPD2_PACK-11_GOVERNED_DOCUMENTS_EVIDENCE_0.11.0_FINAL_PASS.zip` |
| Baseline repository version | `0.11.0`                                                         |
| Canon version               | `0.8.0` — unchanged by this round                                |
| Baseline status             | FINAL PASS, external GitHub Actions verified                     |

PACK-11 remains the historical baseline. Nothing in PACK-11 was rewritten
by this round: `document-service` is untouched, and PACK-12 seals its
session evidence into PACK-11's evidence bundles rather than defining a
parallel evidence system.

## 2. Scope of PACK-12

Privileged administration, authorization-aware search, and governed data
export with data-loss prevention and statistical disclosure control —
`FIR-ROADMAP-002`.

One wholly new service, `services/privileged-access-service`:
**17 source modules, 16 test modules, 327 tests of its own.**

## 3. Bounded contexts implemented

Three logical bounded contexts share **one** package boundary, **one**
command frame and **one** audit path — the resolution of `OD-P12-04`.
They are one control surface: a privileged grant that could be reasoned
about without the search and the export it authorises is a control in
name only, and splitting them would have required three audit paths,
which `OD-P12-06` forbids.

| Context                                  | Aggregates                                                                     | Modules                            |
| ---------------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------- |
| Privileged administration                | `PrivilegedAccessGrant`, `BreakGlassActivation`, `PrivilegedSession`           | `access`, `breakglass`, `sessions` |
| Authorization-aware search               | `QueryAudit`, `IndexPolicy`                                                    | `search`, `classification`         |
| Governed export, DLP, disclosure control | `ExportRequest`, `ExportArtifact`, `DlpAssessment`, `DisclosureRiskAssessment` | `export`, `dlp`, `disclosure`      |

Supporting modules: `exceptions`, `domain`, `policy`, `roles`,
`references`, `events`, `storage`, `application`.

### Guarantees that are structural rather than documented

1. **No bypass exists.** No feature flag, environment switch, deployment
   mode, privileged grant or emergency path disables any invariant, audit
   append or separation check (`roles.NO_BYPASS_NOTE`, FIR-INV-006).
2. **No standing superuser is expressible.** `EffectiveWindow` has no
   "no end" option; no `renew` and no `extend` exist (`P12-PAM-003`).
3. **No universal console.** No role set reaches ballot content or
   mutates an audit record (FIR-INV-014, FIR-INV-002).
4. **PACK-08's incompatibility baseline is preserved and made stricter,
   never relaxed** — one preserved institutional pair plus fourteen
   additions, re-checked at the moment of the act (canon 19e.16).
5. **Separation of duties is evaluated twice** — at approval and again at
   activation (`P12-PAM-005`).
6. **Audit before event.** An event that reached the stream without an
   audit row would be an unaccountable act; `_finish` makes that ordering
   impossible.
7. **No deletion.** No storage port defines a delete-shaped method, with
   one named exception — `SearchIndexStore.remove`, which requires
   `IndexRemovalEvidence`.
8. **No voting reference type is declared** (`P12-VOTE-001`).
9. **Session evidence carries no secret** (`P12-SES-007`).
10. **Export fields are selected, never stripped** (`P12-EXP-008`).

## 4. ADR-061 — ADR-068

All eight are `proposed`. This round amends **no** canon.

| ADR     | Subject                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------ |
| ADR-061 | Privileged role separation — two institutional roles consumed, nine operational assignments introduced |
| ADR-062 | Purpose-scoped privileged access management                                                            |
| ADR-063 | Break-glass dual control, notification obligation, independent review                                  |
| ADR-064 | Authorization-aware search                                                                             |
| ADR-065 | High-confidentiality index exclusion and the classification mapping                                    |
| ADR-066 | Governed data export                                                                                   |
| ADR-067 | DLP and statistical disclosure control                                                                 |
| ADR-068 | Privileged session evidence                                                                            |

Canon 19e.15 keeps `role_code` an open list extensible "by configuration

- ADR review"; canon 19e.16 fixes a _minimum_ pairwise incompatibility
  baseline that may be made stricter and never relaxed. The nine roles
  PACK-12 adds are privileged _operational assignments_, not institutional
  offices, so no canon amendment follows from them —
  `docs/packs/PACK-12/PACK-12-CANON-ASSESSMENT.md` records that verdict.

## 5. FIR treatment

`FIR-ROADMAP-002` → **`implemented`**, on the strength of the external
GitHub Actions PASS recorded in section 8.

Entries given a **foundation only** — each explicitly NOT implemented, and
each carrying that statement in the register:
`FIR-SEARCH-001`, `FIR-SEARCH-002`, `FIR-SEARCH-003`, `FIR-METRIC-002`,
`FIR-ID-002`, `FIR-COMM-004`, `FIR-SEC-001`, `FIR-SEC-003`,
`FIR-ROLE-001`, `FIR-ROLE-003`, `FIR-DATA-001`, `FIR-DATA-003`,
`FIR-FRONT-001`, `FIR-FRONT-002`, `FIR-FRONT-003`, `FIR-INV-011`.

Entries deliberately left **unchanged**: every other entry. In particular
`FIR-INV-002`, `FIR-INV-003` and `FIR-INV-005` are untouched — PACK-12
establishes the structural _absence_ of any voting reference type and adds
no voting semantics. `FIR-INV-010` is untouched: PACK-12 reuses PACK-11's
evidence bundles rather than reimplementing them.

New FIR identifiers created by implementation discovery: **none.**

The canonical FIR coverage matrix has exactly one location:
`docs/packs/PACK-12/PACK-12-FIR-COVERAGE-MATRIX.md`.

## 6. Deferred acceptance criterion

**`AC-P12-090` remains deferred.** It is not satisfied by this round and
is not claimed to be. `AC-P12-019` is closed by the numeric policy in
`policy.py`.

## 7. Corrections that passed through external CI

The candidate was corrected twice before the green run. Both are part of
the verified tree; the candidate reports are retained unmodified as the
historical record of the stages, and are **not** rewritten to read as
though they were always FINAL PASS.

| Round                    | What it did                                                                                                                                                                                                                                                                                                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Documentation correction | Replaced the false "locally verified" claim in the register with an accurate incomplete/pending statement; corrected the module inventory to 17 source / 16 test modules; added the `0.12.0` status banner and PACK-12 section to `README.md`; added superseding status notes to the nine specification documents whose "not implemented" headers had become misleading. 15 files, documentation only. |
| CI format correction 1   | `prettier --write` on 15 files. One change was rejected as a semantic corruption rather than formatting: a line-initial `+` in `docs/adr/README.md` was being parsed as a list bullet and rewrote a sentence into a list; the line break was moved so the `+` is no longer at line start, with no word changed.                                                                                        |
| CI format correction 2   | Removed the stray duplicate `docs/handover/PACK-12-FIR-COVERAGE-MATRIX.md`. Nothing referenced it — not `REQUIRED_PATHS`, not `tests/`, not `Makefile`, not `.github/`, and no Markdown. It was never present in any delivered archive.                                                                                                                                                                |

## 8. External GitHub Actions results

| Check                    | Result                            |
| ------------------------ | --------------------------------- |
| Repository path manifest | **PASS** — 728 / 728              |
| Forbidden paths          | **PASS** — none                   |
| Ruff format              | **PASS**                          |
| Prettier                 | **PASS**                          |
| Ruff lint                | **PASS**                          |
| mypy                     | **PASS**                          |
| TypeScript typecheck     | **PASS**                          |
| Python tests             | **PASS** — 4062 passed, 4 skipped |
| Browser / frontend       | **PASS** — 108 passed             |
| Accessibility checks     | **PASS**                          |
| Visual checks            | **PASS**                          |

Evidence archive: `epd2-civic-os-verification-result(14).zip`, retained
**outside** this repository. No nested ZIP is placed inside the FINAL PASS
archive.

`docs/handover/PACK-12-EXTERNAL-CI-VERIFICATION-RESULT.md` records these
figures and — importantly — states their provenance: the evidence archive
was **not** available in the environment that assembled this archive, so
the figures are recorded as reported rather than re-derived. There is
deliberately no `PACK-12-EXTERNAL-CI-VERIFICATION.log`, because inventing
a transcript nobody produced would be worse than not having one.

## 9. Verification performed in this packaging round

The documents in section 11 changed after the green run, so the
deterministic checks that this environment _can_ run were re-run against
the final tree.

| Check                    | Command                                                                               | Result                                                                                                                                                                                        |
| ------------------------ | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Repository path manifest | `pytest tests/repository/`                                                            | **PASS** — 728 / 728, all unique                                                                                                                                                              |
| Forbidden paths          | `pytest tests/repository/test_forbidden_paths.py`                                     | **PASS** on a fresh extraction of the archive                                                                                                                                                 |
| Version consistency      | `pytest tests/repository/test_version_consistency.py`                                 | **PASS** — `0.12.0` across Python, TypeScript and `CHANGELOG.md`                                                                                                                              |
| Canon amendment state    | `pytest tests/repository/test_canon_0_8_0_amendment.py`                               | **PASS** — canon `0.8.0` unchanged                                                                                                                                                            |
| Ruff lint                | `ruff check .`                                                                        | **PASS**                                                                                                                                                                                      |
| Ruff format              | `ruff format --check .`                                                               | **PASS**                                                                                                                                                                                      |
| mypy                     | every target in `Makefile`                                                            | **PASS**                                                                                                                                                                                      |
| Python tests             | `pytest`                                                                              | **4054 passed, 5 skipped** — reconciles exactly to CI's 4062 / 4 (see below)                                                                                                                  |
| Duplicate files          | content-digest scan of the whole tree                                                 | **PASS** — zero duplicate-content groups; one master register, one FIR coverage matrix, no duplicate ADR filename, no nested archive of any kind                                              |
| Internal links           | resolver over every Markdown link and backticked repository path in PACK-12 documents | **PASS** — three hits are deliberate prose references to the _removed_ stray `docs/handover/PACK-12-FIR-COVERAGE-MATRIX.md`, in sentences stating that it was deleted; no live link is broken |
| SHA-256                  | recomputed for every added and changed file                                           | section 11                                                                                                                                                                                    |

### What could not be run here, and why

`make verify` cannot complete in this environment: the package registries
are unreachable (`403 Forbidden` on PyPI and npm), so
`uv sync --all-groups --frozen`, `uv lock` and `npm ci` all fail. Every
frontend stage therefore could not run locally: Prettier, eslint, `tsc`,
vitest, the Next.js build, and Playwright. **Those results are taken from
the external CI run and are not claimed as locally verified.**

The eight-test difference between the local and CI Python figures is an
artefact of this environment and is fully accounted for:
`tests/contract/test_property_based.py` calls
`pytest.importorskip("hypothesis")`, and `hypothesis` cannot be installed
here, so the module is skipped locally. 4054 + that module = 4062; 5 local
skips − 1 = 4.

Prettier could not be run at the pinned version either — `package-lock.json`
pins `prettier@3.9.6` and only 3.8.1 is obtainable here. The formatting
in the verified tree was produced under that constraint and **passed CI's
own 3.9.6 check**, which settles it.

## 10. Dependencies on later packages, and the frontend boundary

| Owner       | What PACK-12 depends on and does **not** provide                                                                                                                                |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PACK-13** | Production database, durable event bus, canonical schema registry, production search index, release-history persistence. Every adapter in `storage.py` is in-memory.            |
| **PACK-14** | External IAM / identity provider, authentication, MFA, session issuance, HSM / PKI, the external recipient gateway. `AuthorizationPort` is the seam; PACK-12 mints no identity. |
| **PACK-17** | Real out-of-band notification delivery and the incident-response platform. `NotificationPort` is the seam; `ReferenceNotificationAdapter` sends nothing anywhere.               |

**Frontend boundary.** The PACK-12 specification names twelve
administrative surfaces. **None is implemented.** No frontend workspace,
component, route or view model was added. Where no suitable frontend
integration point existed, the round implemented contracts only and
recorded the limitation — `FIR-FRONT-001` and `FIR-FRONT-003` carry the
obligation, and the workspace architecture remains FRONT-PACK's.

## 11. Known limitations

`docs/handover/PACK-12-KNOWN-LIMITATIONS.md` states twelve in full. The
load-bearing ones:

- **Tamper-evident, not tamper-resistant.** The session hash chain makes
  alteration _detectable_; nothing here prevents it. Without an external
  anchor that is the whole of what the integrity model buys.
- **A watermark marks a copy; it does not stop one being made.**
- **Export revocation withdraws authorization** and blocks further
  platform-mediated access. It does not retrieve a delivered copy.
- **A destruction attestation is a recipient's statement**, not a verified
  fact — this platform cannot observe a third party's storage.
- **DLP is a control model, not a detector.** No content inspection is
  performed; a finding carries a reference, never the matched value.
- **The cumulative-release model is bounded** by a policy window and fails
  closed when the release history is unavailable. Disclosure assembled
  from releases beyond the window is not caught.
- **Pseudonymisation is call-scoped**, carries no key, and is not stable
  across exports.

## 12. Production and legal disclaimers

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

PACK-12 does **not** close, provide or activate any of the following, and
no document in this round may be read as claiming otherwise:

- a production database;
- a production search engine;
- an external IAM or identity provider;
- a real DLP provider;
- real notification delivery;
- production session assurance;
- anything in the voting domain;
- legal activation of any workflow.

Nothing here establishes that a privileged act was lawful, that an export
satisfied a legal basis, that a disclosure control met a statistical
authority's standard, or that any record is admissible. Each remains a
human legal judgement made outside this system, recorded here as a
determination with its own authority and reason code — and its absence
recorded as absence.

---

## 13. Files added since the PACK-11 FINAL PASS baseline (58)

| File                                                                                      | SHA-256                                                                                          |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `contracts/reason-codes/pack-12.yml`                                                      | `bc0b003564ecb5290642095bbbb2a83e283eab3f3d2840dde24678e168855350`                               |
| `docs/adr/ADR-061-pack-12-privileged-role-separation.md`                                  | `f6e80fa7356a3d5b40b0f9492c45df34eaaa5f400d1a9c3753a89dcbec69e178`                               |
| `docs/adr/ADR-062-pack-12-purpose-scoped-pam.md`                                          | `6a7eda052d9aaa63d78a8d6024763decd68670d727654998a752aa4a629d861b`                               |
| `docs/adr/ADR-063-pack-12-break-glass-dual-control.md`                                    | `1b3763eb1eed5f2306341cdaf1354555113fa3385bc32596360c0828e86edf02`                               |
| `docs/adr/ADR-064-pack-12-authorization-aware-search.md`                                  | `749eb0cc3c82d8df218e7d71d87d2722aad2f5f641da27e6c7d8717adf5f3c75`                               |
| `docs/adr/ADR-065-pack-12-high-confidentiality-index-exclusion.md`                        | `7f61b45386de76a39bb4bae7fbc6da0c04903ac543edb0dfc0f799c6a3b4d30c`                               |
| `docs/adr/ADR-066-pack-12-governed-data-export.md`                                        | `1d83682581b5c208baf1af01c21ec8d94f0b131d48d1f247cca1e41af027f0df`                               |
| `docs/adr/ADR-067-pack-12-dlp-and-disclosure-control.md`                                  | `8ee5f2831d98661e2fd75b87412f9d43f9840f39d938fe153c3d8e8ccca17065`                               |
| `docs/adr/ADR-068-pack-12-privileged-session-evidence.md`                                 | `7d63267013980701ed1aa1bf892f4239ab5767133c1b0fbb277f275414af3d58`                               |
| `docs/handover/PACK-12-EXTERNAL-CI-VERIFICATION-RESULT.md`                                | `7bdf9dcafa6f958a92d33cb31d951f7253d30e1d4f2e0e98d1734664b12656e2`                               |
| `docs/handover/PACK-12-FINAL-PASS-REPORT.md`                                              | _self-referential — a file cannot contain its own digest; compute it from the delivered archive_ |
| `docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md`                                | `5d2d9dce413d08b940844f6fa60cb1d7cc34cd61e1d495ea08886d5062ac9508`                               |
| `docs/handover/PACK-12-KNOWN-LIMITATIONS.md`                                              | `39d07059370d32346c5368cc325a434d4211f0454c41ca803d6bc5a12e33707a`                               |
| `docs/handover/PACK-12-SPEC-ADR-REPORT.md`                                                | `a8116d3a8a54d7ed45e68312a10cd148f05c406be5395cb1a2a21a52a5d87e9e`                               |
| `docs/packs/PACK-12/PACK-12-ACCEPTANCE-MATRIX.md`                                         | `600bbee567569f04e89ca46c2b346b2bda65ac190ccdb08812fa683c2cd8535e`                               |
| `docs/packs/PACK-12/PACK-12-CANON-ASSESSMENT.md`                                          | `63b9c128f23f515eaafb71dabd451a014e376e6850692770cf25fc3397964db4`                               |
| `docs/packs/PACK-12/PACK-12-DATA-SEARCH-EXPORT-MATRIX.md`                                 | `6b82265baaa4d00489701b8d6a9dd3741965866395e7cf239a9a1d488492a181`                               |
| `docs/packs/PACK-12/PACK-12-EVENT-CATALOG.md`                                             | `3cc30c77c45935756fb7ce81857e4092878dec8517004b61f77ca0400b10758e`                               |
| `docs/packs/PACK-12/PACK-12-FIR-COVERAGE-MATRIX.md`                                       | `2f0a3f2d5cea3ea22b8d9d0b8e8976cbd88a1dd5aa5c6390f7cf9e9c0635c303`                               |
| `docs/packs/PACK-12/PACK-12-REASON-CODE-CATALOG.md`                                       | `dffa018336c011e15e4d1e343ab3a57e0946c423305b25417653c9fa21c34e9e`                               |
| `docs/packs/PACK-12/PACK-12-ROLE-SEPARATION-MATRIX.md`                                    | `2fbb7ee499e11c12b10e0c96c3e876bc712412f68bf48d151fa6e7788ce8795c`                               |
| `docs/packs/PACK-12/PACK-12-SPECIFICATION.md`                                             | `eeec3b9d08d931ce3a94b828a4358b3abb48e24c4cec3ff9d4635d99f722a792`                               |
| `docs/packs/PACK-12/PACK-12-THREAT-MODEL.md`                                              | `eecb302b5ac22bd4121aaeb829fa9ae09d27c9f8fcc0c609cf1d39e45d56e597`                               |
| `services/privileged-access-service/README.md`                                            | `8caf63b7b59615a896a61b705239b18492b10ed6cea1a7a7ba4cb798229e7b47`                               |
| `services/privileged-access-service/pyproject.toml`                                       | `d5af31e116f1c8bb2e4fbdf3fd33084ff9ed49bce53d3c23f64b57c2b1a6f2d5`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/__init__.py`       | `0c2e766fd073f5c8e3ab75a90517d263e97e7ca3ce4fe7680380caaa31a3130e`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/access.py`         | `ae7de8b509f29d85c4b6c17c888400a182efad62d801b3b4f246bd4ec3c8a419`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/application.py`    | `fc4ffe6fa3ace444412b4776ea38d9b809ce7eee969eab8a7b4dc08db5b3f687`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/breakglass.py`     | `ed53c20d881f39628c56d4e4ddb85bfe138462408db90b1c5dfdf23112cb11cf`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/classification.py` | `2a7228110f73337c9b203a1250c50302cc085adcac20c23c271ecf5224875ad2`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/disclosure.py`     | `e5eb315851358302c23772d6a79f7a63619d7aa31b63b550bf7f0e7a401fa5df`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/dlp.py`            | `3219910875d11ef9fc25ac3f85104a7b66ded48195b6b055873c89d66c467f7b`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/domain.py`         | `fa5777735188f550a1771ec68ef5ab3c7163debcb577fdc20f93c90a69d8b4de`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/events.py`         | `cbe6e5f6234bd71c9eb50e45cc72c0d809fc6eb5da60176b18a3e14354882bd3`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/exceptions.py`     | `e6204d1cc9ff7523172ae57b28401353a23daedb20cbf2b5d7493daf91bd1dce`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/export.py`         | `754805f0434f54e6a88ef9042207d712158180b62fbc2084bcba73a75b356b0a`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/policy.py`         | `e31461cdd4565a9ea97add8366b8f526704c79b2543893db81bce14de6189fd4`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/references.py`     | `932e2fa7f13e7521d0e29989e2794b28be640e05a5d1a81889f4d61c3388efaa`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/roles.py`          | `73121629b282ccd40389ab32b7974668f5a5b0291310519087b4938b96ba8fcf`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/search.py`         | `62887810fd4c6625e49e21274351843811cd16c60d93b05267c459804525811d`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/sessions.py`       | `8e3833074ceedd39ff853be365bd2aa3cbb95d625412309be70ba02a0342a5e0`                               |
| `services/privileged-access-service/src/epd2_privileged_access_service/storage.py`        | `742fe84928b85261145c50f9204a14871b0985b063a39d7369ac6f5267b445e0`                               |
| `services/privileged-access-service/tests/_privileged_builders.py`                        | `9e2fa8193c782aaaf042e91b10366d025254e99f53795e6c7a6cedfb0855fb6b`                               |
| `services/privileged-access-service/tests/conftest.py`                                    | `9a627709e2c7f97ee468fd642acdd143df9666835dae7e9b1ed1dddb8f94765a`                               |
| `services/privileged-access-service/tests/test_access.py`                                 | `fc8cc834f873cb21957d7f536d62260bd3debba48e0b7f4a6770b61ab186e21a`                               |
| `services/privileged-access-service/tests/test_application.py`                            | `570bbee233e42e8441a9b1fe3288ee26a7f3f109de678ead198e7a3a42ea6a8b`                               |
| `services/privileged-access-service/tests/test_application_flows.py`                      | `542507822f7bdf100fdf1e660847927c417a37a7d9a74252592baff5c1f984bd`                               |
| `services/privileged-access-service/tests/test_breakglass.py`                             | `f1b63bdbb515f0c463adbc75438123d641b8cd04d0a95eae9f53955a4bf1d1eb`                               |
| `services/privileged-access-service/tests/test_disclosure.py`                             | `28a9af4b45c1eb3542ca516a0181860ed771664b249abfa61e4d8de1ec0094f5`                               |
| `services/privileged-access-service/tests/test_dlp.py`                                    | `49f01d8a0aa49594d60a9cacc6c3f83d976e7fcc62cc7b4e5c3398703470ff08`                               |
| `services/privileged-access-service/tests/test_domain.py`                                 | `6d488b89c72c65fbe0041f83ea4fa0627a7205cbe895ce194af603c0ac0f1ce0`                               |
| `services/privileged-access-service/tests/test_events.py`                                 | `f516c0e739ca156668d4d1043007cdb55c9c4c6818607263b06591d6759f68ca`                               |
| `services/privileged-access-service/tests/test_export.py`                                 | `fdf9719c7f3cfac667246e070f08e2e9cd998fa48de8b0eeb80a75c23894df0c`                               |
| `services/privileged-access-service/tests/test_policy.py`                                 | `d0c9946c2060ff2a70a671ec4f7d1e0e43ad47c14b0e27bc45ddbd8e618cf12f`                               |
| `services/privileged-access-service/tests/test_roles.py`                                  | `d4b0c261707e9fd0977e9d0a17dac484baf7264a3a26549e90363a40732a9600`                               |
| `services/privileged-access-service/tests/test_search.py`                                 | `9ec5e2351e7106dd45c14b3e478dbd42b827b303bd84518da01e8471438b4924`                               |
| `services/privileged-access-service/tests/test_sessions.py`                               | `2fb64a3b2fc4d7ff33e245726b6b9d0de3351396469e77fbe1eabf07e3422297`                               |
| `services/privileged-access-service/tests/test_storage.py`                                | `aca841e4cbcf37e684e77bc06c052e34d28dc6bff8c954c1bda143557543874a`                               |

---

## 14. Files changed since the PACK-11 FINAL PASS baseline (17)

| File                                                         | SHA-256                                                            |
| ------------------------------------------------------------ | ------------------------------------------------------------------ |
| `CHANGELOG.md`                                               | `5faec3df362026cebc58f51421aa09e0569c0ca690b91992efe37378b998bd38` |
| `Makefile`                                                   | `687a353a208619d64021d01d7fe49ab3263cfdcc5b4626bb053aedfe6d699e2f` |
| `README.md`                                                  | `6e7ebce7aad29e39e8ddca08fe3723656de2ae3021c092d943c5b550c4e6e3b2` |
| `docs/adr/README.md`                                         | `8ee58143f6b4160c834a6b40496c96d37e2370ea44a46b21d5fc34285cd240aa` |
| `docs/canonical/canon-version.json`                          | `8f57cb94e87c0fab2f5b95d69c7075451a3cca4b66b93183db02c092a07b8707` |
| `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` | `d5b8dc9628e9c69becff6de732e7bfdcaedc8230f73a3a3ae04dd9239ae2ced6` |
| `packages/python/epd2-core/src/epd2_core/version.py`         | `8b78b9c405a4b0dcb4edcfd6ec554acdd2ebe5eeeaee5903a1900188d5574c78` |
| `packages/python/epd2-core/tests/test_version.py`            | `29aca2274eace5904ad459e1da3aabe2607567052c93d7a450aeb5195033f227` |
| `packages/typescript/epd2-types/src/version.ts`              | `2b10ff85c05ebe3fd8ad0b0ab32c94dc296f162bc7138d8185e1d53b7fd880d8` |
| `packages/typescript/epd2-types/tests/version.test.ts`       | `70ce071eec4a4562655fcc3e3b621de5dabde59d5696216be5afe007ec87347e` |
| `pyproject.toml`                                             | `f08883516b64b754b3f3e20671c45fac38d54b99c8f318b297278142e33478bf` |
| `scripts/check_canon_0_8_0.py`                               | `f1caae6504cfe1ed857b0b23a43bbe64fab087c2d3413c2c6945ea8ae5635fc6` |
| `scripts/check_repository.py`                                | `d07cfe9663e6d553f8bfdaa2aff23e35b389cbd39d48dced5f88beabca489d21` |
| `tests/contract/_schema_helpers.py`                          | `abeebddba99bad1d01cec125792fcfa9306669b4ea30c1948374293556e1af59` |
| `tests/contract/test_reason_codes_registry.py`               | `fb79c6cd35aedabd9ba4e754c1c4cd758df004f2d23de6d8bd11da10598d586a` |
| `tests/repository/test_service_boundaries.py`                | `3471fc5800d5ce3f16e9548f4156995670b588549003c98b24a9917d2199bfde` |
| `uv.lock`                                                    | `8777af7301103e56da94100891d57a6af3ac1a13a382272d74d027faf9ea61e8` |

---

## 15. Files removed

None.

---

## 16. Archive digest

The SHA-256 of the delivered archive is reported in the delivery message
accompanying it, and is deliberately not printed here: a file cannot
contain the digest of the archive that contains it.

```bash
sha256sum EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_FINAL_PASS.zip
```
