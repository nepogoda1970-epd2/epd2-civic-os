# EPD² Program Control Register

**Status:** Living canonical execution-state register  
**Location:** `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`  
**Updated:** 2026-08-26  
**Purpose:** single authoritative source for the current execution state of the EPD² development program.

This register answers what is closed, active, next, blocked, permitted in parallel, and which governed candidate/evidence currently controls each active line. It does not replace the Master Future Implementation Register.

---

## 1. Mandatory bootstrap and authority split

Read first:

1. `docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md`
2. `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`
3. `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`
4. current stage contract / handover named by this register.

Current execution state is governed here. Future requirements and hard invariants are governed by the Master Future Implementation Register.

Current Master maintenance level established by project governance work: **V16**, including `FIR-UX-012` and `FIR-UX-013`.

**Repository reconciliation note (superseded 2026-08-25, API-01 C3/C4 governance reconciliation):** the exact V16 repository reconciliation is **COMPLETED**. The Master Register inspected when this control register was introduced predated the V16 maintenance copy; that condition no longer holds. The canonical Master Future Implementation Register is the reconciled current repository Master (`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`, maintenance copy **V16**, sha256 `0a6a97a3ed04e78b7d925e750c2b99954b7e2c04b143f48ed28be7572b809c14`): the V15/V16 maintenance additions (`FIR-UX-012`, `FIR-UX-013`, update records carried as sections 1.66/1.67) are integrated into the newer repository history, no newer repository state was downgraded, and no V16-specific FIR state was inferred or reduced (record: `docs/api/API-01/API01_MASTER_REGISTER_RECONCILIATION.json`; this register's own transition: `docs/api/API-01/API01_PROGRAM_CONTROL_RECONCILIATION.json`). Reconciliation state: **COMPLETE / CURRENT**.

On 2026-08-26 API-01 completed independent authoritative acceptance. Exact candidate `EPD2_API01_PRODUCTION_API_GATEWAY_AND_BFF_BOUNDARIES_CANDIDATE_0.1_C5.zip`, sha256 `cea2fb0e23ee174e802ec1899cf62e570e5c8659a0f31c7e6c3c3955bffa3d27`, passed GitHub Actions workflow `api01-accept`, authoritative run `32967210855`, conclusion `success`. API-01 is therefore `ACCEPTED / CLOSED`; API-02 is the next permitted primary API stage.

---

## 2. Program phase state

| Program layer | Current control state | Execution rule |
| --- | --- | --- |
| ARCH PACK-01…35 | `CLOSED` | Do not restart architecture PACK sequencing as current work. |
| DATA | `CLOSED` | Do not describe DATA as still being finished unless a governed correction explicitly reopens it. |
| API | `API-01 ACCEPTED / CLOSED; API-02 NEXT` | API-01 is closed by authoritative run `32967210855`; API-02 is the next primary API stage. |
| INFRA | `NOT_STARTED` | Preparation/specification may proceed; final closure follows API dependencies. |
| OPS | `NOT_STARTED` | Procedures/runbooks may be prepared; runtime closure follows INFRA. |
| CTRL | `NOT_STARTED` | Control-plane specifications may be prepared; integrated closure follows OPS/INFRA. |
| FRONT | `FRONT-02_SPECIFIED / NOT_STARTED_FINAL` | FRONT-02 specification is established and may be implemented in parallel within its governed scope; final integrated journeys follow runtime/control-plane dependencies. |
| SEC | `NOT_STARTED_FINAL` | Threat/adversarial preparation may proceed; final challenge targets the integrated system. |
| PILOT | `PARALLEL_DEVELOPMENT_EXISTS` | PILOT-01…05 have existing lineage/work. Exact stage state is governed below. |

Canonical primary closure sequence:

```text
DATA → API → INFRA → OPS → CTRL → FRONT → SEC
```

Current primary position:

```text
DATA = CLOSED
API-01 = ACCEPTED / CLOSED
API-02 = NEXT
```

This does not prohibit already-existing or corrective parallel PILOT work or the governed parallel FRONT-02 implementation preparation described below.

---

## 3. Parallel work currently permitted

While API-02 is the next primary API stage, the following may proceed without changing `API-02 = NEXT`:

- INFRA specifications, environment/container topology, CI/CD and deployment design;
- OPS incident/recovery/change/election runbooks and SoD models;
- CTRL action/authority inventories, read models and control-console specifications;
- FRONT shared design/application shells, public pages, accessibility/responsive baselines and non-misleading read-only surfaces, now governed by `docs/frontend/FRONT-02-SPECIFICATION.md`;
- SEC threat-model consolidation, adversarial corpora and test-harness preparation;
- governed correction/acceptance work on already-existing PILOT stages.

Parallel work must not claim `CLOSED`, `PASS`, `ACCEPTED`, `PRODUCTION_READY` or `LEGALLY_ACTIVATED` before its governed acceptance gate.

---

## 4. PILOT execution state

Canonical meanings remain locked by `docs/roadmap/EPD2_PILOT_ROADMAP_LOCK.md`.

### PILOT-01 — Internal Organization Pilot

**Control state:** `COMPLETED_IN_INHERITED_ACCEPTED_LINEAGE`

PILOT-01 functionality/history is inherited by later accepted cumulative PILOT baselines. If an exact original PILOT-01 candidate SHA is required, reopen historical evidence rather than guessing.

### PILOT-02 — Membership & Participation Pilot

**Control state:** `ACCEPTED_HISTORY / SUPERSEDED_AS_CURRENT_BASELINE`

Accepted immutable predecessor recorded by the roadmap lock:

`EPD2_PILOT02_PUBLIC_SITE_INTEGRATION_AND_UNIFIED_PILOT_PRODUCT_CANDIDATE_0.51.2_C4.zip`

SHA-256: `261ab0996659f453d3d6d3cf43e12ad105fa6dbacd5035de40ca949029cbfc3e`

Historical stale next-gate guidance inside that accepted archive is superseded by the current PILOT roadmap lock.

### PILOT-03 — Assemblies / Motions / Communications Pilot

**Control state:** `ACCEPTED / ESTABLISHED`

Accepted cumulative application baseline:

`EPD2_PILOT03_ASSEMBLIES_MOTIONS_AND_COMMUNICATIONS_CANDIDATE_0.1_C3.zip`

SHA-256: `52b5bbfe312d90d65f500f0b6085d33ffe3235ce4bd90562110a26a8fae208d1`

### PILOT-04 — Non-binding Digital Vote Pilot

**Control state:** `DEVELOPED / NOT ACCEPTED_FROZEN`

The preserved corrective line reaches at least C9. Preserved C9 evidence records local PASS/readiness for independent GitHub acceptance, but not authoritative GitHub PASS and not `ACCEPTED_FROZEN`.

PILOT-05's stage-entry predecessor pin is exact PILOT-04 C7:

`EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C7.zip`

SHA-256: `812652950e996bd7c781512e4bbc03488c58eb74ca0c652c2b830056d76c1f1d`

The PILOT-05 C3 lineage separately records PILOT-04 C9 as application-line alignment:

`EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C9.zip`

SHA-256: `7fc4f3a5a982d11535006fcea8201ffb694546a01f5326eaed09fcf4ffc78664`

### PILOT-05 — Representative Desk / Transparency Pilot

**Control state:** `C3 CANDIDATE / GOVERNANCE-STATIC PASS / FULL LIVE ACCEPTANCE NOT YET PROVEN`

PILOT-05 is substantial implemented product work. It must not be restarted from zero.

#### Historical C2 working state

The preserved C2 corrective working state had one cumulative root with 3728 members and reassembled SHA-256:

`eb1fc9be21b479a07fd76c082d9964343049f6ba2b0f319677f8d4b9b74515c9`

It carried the F-01/F-02 corrections but was not acceptance-ready because its root identified C2 while the governed dossier/validator still identified C1.

F-01: true two-principal publication approval, including migration `0015_pilot05_two_principal_approval.sql`.

F-02: constituent correlation boundary using external keyed pseudonym/HMAC handling, including migration `0016_pilot05_constituent_correlation_boundary.sql`.

#### Current C3 candidate

On 2026-08-25 the supplied two-part C3 was reassembled and independently inspected as:

`EPD2_PILOT05_REPRESENTATIVE_DESK_AND_TRANSPARENCY_PILOT_CANDIDATE_0.1_C3.zip`

Reassembled archive SHA-256:

`fc3f371bcf180e6559bc8ccc72cb74a88deef293f768424bcae7576731e8d8fb`

Archive member count: `3744`

ZIP integrity: `PASS` (single root, CRC/testzip clean).

C3 now contains and correctly binds:

- `docs/pilot/PILOT-05/PILOT05_C3_LINEAGE.json` as `CURRENT` authority;
- `docs/pilot/PILOT-05/PILOT05_C2_LINEAGE.json` as historical working-state record;
- preserved C1 lineage/validator as historical artifacts only;
- `docs/pilot/PILOT-05/PILOT05_C1_TO_C2_EXACT_INVENTORY.json`;
- `docs/pilot/PILOT-05/PILOT05_C2_TO_C3_EXACT_INVENTORY.json`;
- `docs/pilot/PILOT-05/PILOT05_C3_MANDATORY_TESTS.json`;
- `scripts/validate_pilot05_c3.py`;
- frozen evidence under `evidence/pilot05-c2/`;
- historical banners on superseded C1 dossier documents.

Measured C2→C3 inventory:

```text
unchanged 3713
added       16
modified    15
removed      0
```

The C3 validator's independent `--static-only` run passed all static/governance checks, including:

- correct root/stage identity;
- exact roadmap-lock digests;
- C3 CURRENT authority and C1/C2 historical status;
- all 3744 tree paths bound by the exact inventory;
- no unrelated drift outside the declared reconciliation allowlist;
- 3743 SHA256SUMS entries verified in both directions;
- F-01/F-02 migrations registered;
- no committed correlation key material;
- exact nine F-01 adversarial tests and eight F-02 unlinkability tests named.

Terminal result of that independent static run:

`PILOT05_C3_RESULT:STATIC_ONLY_PASS:<evidence-path>`

A full independent validator run was also attempted. It failed closed at the mandatory database prerequisite because the verification environment did not provide `EPD2_TEST_DATABASE_URL`:

`B1.database = FAIL: EPD2_TEST_DATABASE_URL is not set — live proof is mandatory`

Terminal result:

`PILOT05_C3_RESULT:FAIL:<evidence-path>`

This is **not evidence of a product defect**, but it means full live acceptance has not yet been independently proven. Therefore C3 must not yet be promoted to `ACCEPTED` solely from the static PASS or from its bundled pre-seal evidence.

The C3 lineage explicitly records the integration context: existing `INTEGRATION-01 C4` remains immutable and is not modified by PILOT-05 C3; an independently accepted PILOT-05 result is intended to become the application-line predecessor for a later `INTEGRATION-01 C5`.

### PILOT-06 — Pilot Findings & Corrections

**Control state:** `NOT_STARTED_AS_GOVERNED_STAGE`

Do not open PILOT-06 merely because corrective rounds occurred inside PILOT-04 or PILOT-05.

### PILOT-07 — Production Readiness Decision

**Control state:** `NOT_STARTED`

No production-readiness decision is implied by existing PILOT work.

---

## 5. Frontend governance notes

### FRONT-02 — Design System, Application Shells & Page/Route Governance

**Control state:** `SPECIFICATION ESTABLISHED / IMPLEMENTATION NOT STARTED`

Governing specification:

`docs/frontend/FRONT-02-SPECIFICATION.md`

Route reconciliation:

`docs/frontend/FRONT-02-PUBLIC-PAGE-ROUTE-DECISIONS.csv`

The specification preserves the accepted FRONT-00/FRONT-01 visual baseline, the ten-workspace/ten-origin architecture and WS-03 voting isolation. It establishes the route-authority order and requires German public-route continuity for WS-01. It also records the required public page families for Presse, Termine, complete Aktuelles detail pages, Regionen, approved public Personen, Wahlen, Hilfe and public search, plus mandatory system/failure/recovery states.

No new FIR ID is required: these obligations are governed by existing `FIR-UX-003…013`, `FIR-SEARCH-001…003`, `FIR-SUPPORT-001…003`, `FIR-FRONT-001/002` and related invariants. Because this specification introduces no new future requirement and promotes no FIR status, the canonical Master Register is not changed by FRONT-02 itself.

FRONT-02 implementation candidate must not start until the derived page catalogue, page sequence, navigation, content/action maps, screen-state matrix, permission/assurance matrix, responsive specification, accessibility flow and acceptance-screenshot inventory required by `FIR-UX-011` exist and are internally consistent.

### V15/V16 carried requirements

The current Master maintenance line includes:

- `FIR-UX-012 — Public Transparency Information Architecture & Verification Surface`;
- `FIR-UX-013 — Global EPD² Identity Line`.

Exact global public identity expansion: `Erste Partei Direkte Demokratie` beneath the standard upper-left `EPD²` logo on every public page using the shared header, without redesigning the logo or public visual baseline.

These are governance requirements and do not themselves constitute frontend acceptance.

---

## 6. Status-change discipline

A layer or PILOT stage may move to `CLOSED`, `ACCEPTED` or `ESTABLISHED` only when governed evidence for that exact stage supports it.

Every status transition must record previous/new state, governing artifact or commit, immutable identity where applicable, verification evidence, open blockers, and next permitted primary stage.

No status may change merely because a conversation says it is convenient.

### API-01 authoritative transition — 2026-08-26

- **Previous state:** `API-01 C5 CANDIDATE / CANDIDATE_NOT_ACCEPTED`.
- **New state:** `API-01 ACCEPTED / CLOSED`.
- **Governing candidate:** `EPD2_API01_PRODUCTION_API_GATEWAY_AND_BFF_BOUNDARIES_CANDIDATE_0.1_C5.zip`.
- **Candidate SHA-256:** `cea2fb0e23ee174e802ec1899cf62e570e5c8659a0f31c7e6c3c3955bffa3d27`.
- **Authoritative workflow:** `.github/workflows/api01-accept.yml`, exact packaged Git blob `123be8088812d772cb3c2ee138a56873934924cc`.
- **Authoritative run:** GitHub Actions `32967210855`, conclusion `success`, provenance commit `565310344f1e8c67d725b721aad29d94a5f7f6f7`.
- **Validator terminal result:** `API01_RESULT:PASS:validation/api01/validator_result.json`.
- **Authoritative evidence artifact:** `api01-c5-acceptance-evidence-32967210855`, artifact ID `9606736122`, SHA-256 `88fdd20fc7239eb5dfc9f66b4d3ddd5aadae013e726269b24454605a557ba8bd`.
- **Inherited DATA-06 semantics:** PostgreSQL 16.15 Phase B remains `3 failed, 203 passed, 32 skipped`; `new_failures = 0`; result semantics `NO_NEW_REGRESSION_AGAINST_ACCEPTED_DATA06_BASELINE`.
- **Browser gate:** PASS with frozen Playwright `1.62.0`, mechanically resolved Chromium, fail-open suppression `false`.
- **Runtime route truth:** 63 routes, runtime-derived and registry-consistent.
- **Mutation suite:** 28/28 fixtures detected.
- **Open blockers for API-01:** none.
- **Next permitted primary stage:** `API-02 — Authentication & Authorization Runtime`.

---

## 7. Branch / reconciliation discipline

There is exactly one canonical Program Control Register. A branch reads the target/current register as entering state, changes only evidence-supported facts, never silently resets newer state, and never creates a competing control register. At merge, reconcile against the target branch's current copy.

---

## 8. Required repository gate

Governed cumulative candidates should fail when any canonical bootstrap/control/master file is absent, a competing register exists, the control register contradicts the candidate's governed stage, or the register is stale after a status transition.

---

## 9. Immediate execution decision

**Primary implementation:** `API-02 = NEXT` (`API-01 = ACCEPTED / CLOSED`).

**Parallel FRONT action:** FRONT-02 specification is established. The next legitimate FRONT-02 step is completion/acceptance of the mandatory specification artefacts named in `FRONT-02-SPECIFICATION.md`, followed by implementation within that scope. This does not change `API-02 = NEXT` and does not constitute FRONT acceptance or final closure.

**Parallel PILOT action:** PILOT-05 C3 governance reconciliation is now materially complete and independently static-verified. The next legitimate PILOT-05 step is a full live independent acceptance run with its mandatory database/runtime prerequisites. Only after that PASS may C3 become the accepted application-line predecessor for `INTEGRATION-01 C5`.
