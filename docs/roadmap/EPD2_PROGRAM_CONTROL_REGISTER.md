# EPD² Program Control Register

**Status:** Living canonical execution-state register  
**Location:** `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`  
**Updated:** 2026-08-27  
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

Current Master maintenance level established by project governance work: **V24**, including `FIR-UX-012`, `FIR-UX-013`, `FIR-AI-003` with its governed implementation-placement matrix, `FIR-GOV-004` Regional Authority Suspension & Intervention Control, and `FIR-SEC-004` Governed Access, Credential & Key Authority Lifecycle Control.

**Repository reconciliation note (superseded 2026-08-25, API-01 C3/C4 governance reconciliation):** the exact V16 repository reconciliation is **COMPLETED**. The Master Register inspected when this control register was introduced predated the V16 maintenance copy; that condition no longer holds. At that reconciliation point, the canonical Master Future Implementation Register was the reconciled repository Master (`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`, maintenance copy **V16**, sha256 `0a6a97a3ed04e78b7d925e750c2b99954b7e2c04b143f48ed28be7572b809c14`): the V15/V16 maintenance additions (`FIR-UX-012`, `FIR-UX-013`, update records carried as sections 1.66/1.67) are integrated into the newer repository history, no newer repository state was downgraded, and no V16-specific FIR state was inferred or reduced (record: `docs/api/API-01/API01_MASTER_REGISTER_RECONCILIATION.json`; this register's own transition: `docs/api/API-01/API01_PROGRAM_CONTROL_RECONCILIATION.json`). V16 reconciliation state: **COMPLETE**.

**Documentation-only V17 governance update (2026-08-27):** `FIR-AI-003 — Governed Correspondence Analysis & Reply Drafting` is now recorded in the canonical Master Future Implementation Register. Canonical Master SHA-256 after this update: `fe6b9c63088865ea1af4bce1fb8371c6abc6c0f21174c50ee52cce86c80b849a`. This update changes no execution-stage status, does not implement or activate the capability, and does not alter the primary position: **`API-02 = NEXT`**.

**Documentation-only V18 governance refinement (2026-08-27):** `FIR-AI-003` now contains a mandatory cross-layer Implementation Placement Matrix covering authoritative correspondence/casework ownership, AI processing, documents/evidence, API, INFRA, OPS, CTRL, FRONT, FINAL INTEGRATION and SEC. Canonical Master SHA-256 after this refinement: `5776d8bc49ad3b8c076a057d072c02abe7ad77203b5258ecf4770963ca6eba56`. No execution-stage status changes; **`API-02 = NEXT`** remains unchanged, and exact allocation among API-02…API-06 remains stage-contract governed.

**Documentation-only V19 governance update (2026-08-27):** `FIR-GOV-004 — Regional Authority Suspension & Intervention Control` is now recorded as an approved critical future requirement. It defines four bounded intervention levels — session quarantine, authority suspension, exact regional action restriction and narrow time-bounded temporary supervision — while prohibiting a universal `region_disabled` switch, implicit Bund takeover, voting-domain bypass and rewriting of historical evidence. Canonical Master SHA-256 after this update: `49d9be302bf027c6cda72805f67a9066d8dd5b7453ffab499b75ec1da34797ce`. This documentation update implements or activates no intervention capability and accepts/closes no implementation stage.

**Documentation-only V20 governance update (2026-08-28):** `FIR-SEC-004 — Governed Access, Credential & Key Authority Lifecycle Control` is now recorded as an approved critical future requirement. It separates human credentials, recovery, sessions, organizational authority, privileged JIT/break-glass, service credentials, platform cryptographic keys/provider secrets and voting-domain keys; defines separate request/approval/execution-custody/secret-visibility/review rights; and establishes planned rotation, emergency compromise, signing/trust-set, encryption-key, TLS/certificate, service-credential and human-recovery protocols. Canonical Master SHA-256 after this update: `11b2fd73824e045aac010b41025ffab58e5c7bb637b1e4e5505885dc58b91ae5`. This documentation update activates no key-management capability and accepts/closes no implementation stage. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; exact API-stage allocation remains stage-contract governed.

**Documentation-only V21 governance update (2026-08-28):** `FIR-GOV-005 — Statutory Party-Organ Competence & Digital Authority Binding` is now recorded as an approved critical future requirement. It binds future Civic OS `OrganizationalAuthority` to the exact adopted party-organ competence, rule version, source election/appointment/decision and scope; rejects hierarchy-based inherited administration; and records the governed party-organ competence model plus a non-adopted Satzung 0.3 amendment proposal covering regional autonomy, organs, territorial member assignment, intervention competence and digital authority binding. Canonical Master SHA-256 after this update: `e64a5388006e3f25f89b4d93a4e6a888a9227558df1fcb6eee90816560c07c01`. The technical/governance target is approved; the accompanying Satzung language is **NOT ADOPTED / NOT LEGALLY ACTIVATED** and requires competent party adoption after legal review. This documentation update accepts/closes no implementation stage. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; exact implementation placement remains stage-contract governed.

**Documentation-only V22 governance update (2026-08-28):** `FIR-TRUST-002 — Resilient Trust, Delegated Regional Issuance, Recovery & Immutable Audit` is now recorded as an approved critical future requirement. It establishes technology-neutral bounded regional trust/issuance, separates authoritative `OrganizationalAuthority` from short-lived signed runtime projections, prevents the central root/master key from becoming the hot path of ordinary regional work, defines Security containment deadlock boundaries, key-class-specific threshold custody, quorum-loss/root recovery ceremonies, explicit future RTO/RPO/autonomy targets and externally anchored immutable audit. It does not mandate DID, Keycloak, Vault, blockchain or a specific HSM/KMS provider. Canonical Master SHA-256 after this update: `124c326bd95cfb8821532479b530b306dd020983f873b3f0d924873bd4d0e6d5`. This documentation update implements/activates no trust provider and accepts/closes no implementation stage. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; exact implementation placement remains stage-contract governed.

**Documentation-only V23 governance update (2026-08-28):** `FIR-TRUST-003 — Cryptographic Key Classes, Algorithm Profiles & Crypto-Agility` is now recorded as an approved critical future requirement. The generic platform baseline fixes ES384/P-384 for root/intermediate/regional trust and high-impact audit signing; ES256/P-256 for short-lived authority/service JWS assertions; X.509/mTLS workload identity; WebAuthn ES256 as the mandatory offered passkey profile; AES-256-GCM application/envelope encryption; strict JOSE/JWKS key/algorithm/trust-location validation; class-specific cryptoperiod ceilings; and an inactive ML-KEM-768/ML-DSA-65 migration track. Concrete HSM/KMS/PKI provider selection remains INFRA-owned and PACK-16 voting cryptography is unchanged. Canonical Master SHA-256 after this update: `502ddd3ed8c3bf55e3847145772b0863ded01fdcd8521f4c3debf857d0cc0503`. API-02 remains `ACTIVE / IN DEVELOPMENT` and must reconcile with V23 before acceptance. API-03 remains `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; PRE-SEAL work may continue, but API-03 C1 seal is blocked until exact V23 S2S reconciliation on the exact independently accepted API-02 bytes. This documentation update implements/activates no provider and accepts/closes no implementation stage.

**Documentation-only V24 governance update (2026-08-29):** `FIR-OSS-007 — Open Trust Core & Commercial Operations Boundary` is now recorded as an approved critical future requirement. It fixes the boundary between a publicly inspectable trust core and commercial operational capabilities: verification-relevant protocol semantics, crypto/reference verification code, canonical encodings/test vectors, minimal reference voting client, independent verifier, guardian/key-ceremony protocol and evidence, election-record/finalization semantics and public audit-integrity verification remain open; managed hosting/orchestration, enterprise/admin/guardian UX, HA/resilience, HSM/KMS and government integrations, observability, compliance tooling, hardened/certified distributions, SLA/support and professional services may be commercial only where they are not required to establish cryptographic truth. `FIR-OSS-001` remains controlling: `EUPL-1.2` is unchanged as the intended original-project licence baseline subject to legal review; this update does not select Apache-2.0, relicense existing source or declare EUPL-covered code proprietary. Canonical Master SHA-256 after this update: `ac212cdd32c843a1403b069b51ea6e68a1f120ddadad414a50a0cbad35990e33`. PACK-15/16 voting isolation/cryptography remain unchanged. No execution-stage status changes; `API-02 = ACTIVE / IN DEVELOPMENT` and `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`.

**API-02 execution-state reconciliation (2026-08-27):** the project owner confirms that `API-02 — Authentication & Authorization Runtime` implementation is already underway. The current control state is therefore **`API-02 = ACTIVE / IN DEVELOPMENT`**, not `NEXT`. The existing `handoff/api-02` branch is intentionally reserved as a clean future candidate-verification/upload slot and is not the development branch, candidate evidence, PASS or acceptance record. Historical dated statements that API-02 was `NEXT` remain preserved as history and are superseded only for current-state interpretation. No API-02 PASS/ACCEPTED/CLOSED claim is made. `API-03` may proceed only as **`PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`** and may not be accepted or closed before authoritative API-02 acceptance.


On 2026-08-26 API-01 completed independent authoritative acceptance. Exact candidate `EPD2_API01_PRODUCTION_API_GATEWAY_AND_BFF_BOUNDARIES_CANDIDATE_0.1_C5.zip`, sha256 `cea2fb0e23ee174e802ec1899cf62e570e5c8659a0f31c7e6c3c3955bffa3d27`, passed GitHub Actions workflow `api01-accept`, authoritative run `32967210855`, conclusion `success`. API-01 is therefore `ACCEPTED / CLOSED`; API-02 is the next permitted primary API stage.

On 2026-08-26 the previously stale PILOT-05 control state was reconciled to its already-completed full live authoritative evidence: exact C3 sha256 `fc3f371bcf180e6559bc8ccc72cb74a88deef293f768424bcae7576731e8d8fb` passed GitHub Actions run `32855264419`, conclusion `success`, with `3109 passed, 1 skipped, 0 failed`, F-01 `9/9 PASS` and F-02 `8/8 PASS`. PILOT-05 is therefore `ACCEPTED / ESTABLISHED`; this does not alter `API-02 = NEXT`.

---

## 2. Program phase state

| Program layer | Current control state | Execution rule |
| --- | --- | --- |
| ARCH PACK-01…35 | `CLOSED` | Do not restart architecture PACK sequencing as current work. |
| DATA | `CLOSED` | Do not describe DATA as still being finished unless a governed correction explicitly reopens it. |
| API | `API-01 ACCEPTED / CLOSED; API-02 ACTIVE / IN DEVELOPMENT; API-03 PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED` | API-02 implementation is active. API-03 may proceed only as parallel PRE-SEAL and cannot be accepted/closed before authoritative API-02 acceptance. |
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
API-02 = ACTIVE / IN DEVELOPMENT
API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED
```

### 2.1 Governed execution path with intermediate system trial

The canonical layer order above is unchanged. The following checkpoint-aware execution path governs how the remaining work is to be exposed as a usable system while preserving independent layer acceptance:

```text
DATA CLOSED
  → API-01 CLOSED
  → API-02
  → API-03
  → API-04
  → API-05
  → API-06
  → API CLOSED
  → INFRA/OPS PREVIEW-READINESS MINIMUM
  → SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK
  → INFRA CLOSED
  → OPS CLOSED
  → CTRL CLOSED
  → FRONT CLOSED
  → FINAL INTEGRATION
  → SEC
  → FINAL READINESS DECISION
```

The checkpoint semantics are mandatory:

1. **`SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK` is not a new architecture layer and is not a closure/acceptance state.** It is the first browser-accessible, end-to-end trial of EPD² on the real accepted API runtime and a minimally deployable INFRA/OPS environment.
2. The trial may start only after **API-06 has authoritative acceptance and the API layer is `CLOSED`**, and after the minimum INFRA/OPS capabilities required to deploy, operate, observe, recover and reset the trial environment exist and are explicitly recorded as preview-readiness prerequisites.
3. Preview-readiness does **not** mean `INFRA = CLOSED` or `OPS = CLOSED`. No layer status is promoted by the existence or success of the trial.
4. The trial should exercise real browser journeys and real backend/runtime paths, including authentication/session behaviour, participation/application flows already supported by the accepted runtime, existing pilot functionality where lawfully and technically available, non-binding voting isolation, representative/transparency surfaces, failure states and recovery/operational handling. The exact trial scope is governed when the preview checkpoint is opened; unsupported future functionality must not be simulated as complete.
5. Findings from the trial are routed back to the owning layer and corrected through normal governed candidate/acceptance lineage. Trial findings do not silently mutate accepted baselines.
6. After the trial, the primary closure path resumes: **INFRA → OPS → CTRL → FRONT**. The trial does not replace any of these stages.
7. **`FINAL INTEGRATION` is a cross-layer acceptance checkpoint, not a new architecture layer.** It occurs only after FRONT is closed and before final SEC. It proves the exact integrated baseline across accepted DATA/API/INFRA/OPS/CTRL/FRONT layers and the relevant accepted PILOT/application lineage.
8. Final SEC challenges the **exact final integrated baseline**, not the earlier trial preview. If SEC finds a defect, correct it in the owning layer, re-run the affected integration gates, establish a new exact integrated baseline where necessary, and re-run the affected SEC gates before readiness can be decided.
9. Existing `INTEGRATION-01` artifacts remain preserved historical/parallel lineage. They are not discarded, but further authoritative `INTEGRATION-01` advancement is **not required after every individual API or infrastructure stage**. A targeted integration proof may still be opened earlier if a concrete compatibility blocker requires it.
10. Existing `PILOT-04` / `PILOT-05` work remains governed by its own lineage. The system trial neither renames those stages nor grants them acceptance automatically. `PILOT-06` retains its existing meaning (`Pilot Findings & Corrections`) and is **not** the name of the system-trial checkpoint.
11. This execution-path decision creates no new FIR ID and changes no FIR status by itself. It is a Program Control execution decision; future requirements and invariants remain owned by the canonical Master Future Implementation Register.

This does not prohibit already-existing or corrective parallel PILOT work or the governed parallel FRONT-02 implementation preparation described below.

---

## 3. Parallel work currently permitted

While API-02 is the active primary API stage, the following may proceed without changing `API-02 = ACTIVE / IN DEVELOPMENT`; API-03 is additionally permitted only as `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED` and cannot be accepted/closed before API-02:

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

**Control state:** `ACCEPTED / FROZEN`

The exact C9 candidate is the frozen PILOT-04 baseline:

`EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C9.zip`

SHA-256: `7fc4f3a5a982d11535006fcea8201ffb694546a01f5326eaed09fcf4ffc78664`  
Size: `38,658,195` bytes.

Independent GitHub Actions authoritative verification completed successfully in run `32601698352` using `.github/workflows/pilot04-c9-accept.yml` (workflow Git blob `59bdbffff589f23aa981d755d4d9ca628171f992`). The run concluded `success`; its governed evidence state is `GITHUB_AUTHORITATIVE_PASS`, overall status `PASS`, exit code `0`, result digest `42163788bbeac04522d525cee99e254c1baef98d9d2b1f8fa8fe4692373c4a23`. Mandatory properties passed A `29/29`, B `10/10`, C `8/8`, D `25/25`, E `PASS`, F `9/9`, G `494/494`.

Authoritative evidence artifact: `pilot04-c9-authoritative-evidence`, artifact ID `9483475935`, artifact ZIP SHA-256 `5e7ac279069415fc7ff7007a59012f390ae16648abb46f25e8f0aebb63a4b3b4`. Exact accepted-candidate artifact: `pilot04-c9-exact-accepted-candidate`, artifact ID `9483476323`, artifact ZIP SHA-256 `8182abd5cf0f871475ab613f7e70b81ef5e3e1e2f2c17ed77004e5b75cb21cb0`. The exact candidate bytes were independently rehashed again on 2026-08-26 and matched the governed C9 SHA above.

The authoritative runner deliberately labelled its own output `NOT_FROZEN` because an execution cannot issue its own acceptance decision. The post-run governance decision is now recorded in `docs/pilot/PILOT-04/PILOT04_C9_FROZEN_ACCEPTANCE_RECORD.json` (governance commit `49a1082fd3a46107b71deb4293308691bd1d306e`), which supplies the missing `ACCEPTED_FROZEN` decision without changing or re-running C9. No open PILOT-04 blocker remains.

PILOT-05's original stage-entry predecessor pin to exact PILOT-04 C7 remains a historical lineage fact:

`EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C7.zip`

SHA-256: `812652950e996bd7c781512e4bbc03488c58eb74ca0c652c2b830056d76c1f1d`

That historical pin does not override the current frozen PILOT-04 C9 baseline and does not automatically promote PILOT-05.

### PILOT-05 — Representative Desk / Transparency Pilot

**Control state:** `ACCEPTED / ESTABLISHED`

PILOT-05 C3 is the accepted application-line baseline. The exact accepted candidate is:

`EPD2_PILOT05_REPRESENTATIVE_DESK_AND_TRANSPARENCY_PILOT_CANDIDATE_0.1_C3.zip`

SHA-256:

`fc3f371bcf180e6559bc8ccc72cb74a88deef293f768424bcae7576731e8d8fb`

Archive member count: `3744`.

#### Historical C2 working state

The preserved C2 corrective working state had one cumulative root with 3728 members and reassembled SHA-256:

`eb1fc9be21b479a07fd76c082d9964343049f6ba2b0f319677f8d4b9b74515c9`

It carried the F-01/F-02 corrections but was not acceptance-ready because its root identified C2 while the governed dossier/validator still identified C1.

F-01: true two-principal publication approval, including migration `0015_pilot05_two_principal_approval.sql`.

F-02: constituent correlation boundary using external keyed pseudonym/HMAC handling, including migration `0016_pilot05_constituent_correlation_boundary.sql`.

#### C3 lineage and governance reconciliation

C3 was reassembled and independently inspected as a single-root, CRC-clean cumulative candidate. It binds:

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

An earlier independent full-validator attempt failed closed before live proof because its verification environment did not provide `EPD2_TEST_DATABASE_URL`. That historical environment blocker did not demonstrate a product defect and is superseded for acceptance purposes by the later successful full live authoritative run below.

#### Full live authoritative acceptance

GitHub Actions run `32855264419`, workflow `PILOT-05 C3 terminal acceptance`, completed with conclusion `success` on 2026-08-26. The authoritative job `97825564426` completed successfully with the database/runtime prerequisites, exact Playwright/Chromium preparation and full acceptance validator enabled.

The full validator ran in `FULL` mode (`static_only = false`) and emitted:

`PILOT05_C3_RESULT:PASS:/tmp/pilot05-c3-authoritative-evidence`

Measured live test result: `3109 passed, 1 skipped, 0 failed`. Mandatory execution evidence passed; F-01 adversarial proof is `9/9 PASS`; F-02 unlinkability proof is `8/8 PASS`; all governance checks passed.

Authoritative evidence artifact: `pilot05-c3-authoritative-evidence-32855264419`, artifact ID `9578226563`, GitHub artifact digest `sha256:b36c48cc4c9ef27ab2adb64a3cda7a94b48824b6c2688fb3f5d1c9bae3e5af2d`.

Exact accepted-candidate artifact: `pilot05-c3-exact-accepted-candidate`, artifact ID `9578227300`, GitHub artifact digest `sha256:16194743369291fc0699640539283946822a56bca42f07c99eb02a8a76f731ee`.

The candidate's own `CANDIDATE_NOT_ACCEPTED` self-state remains a valid no-self-acceptance safeguard and is superseded only by this independent post-run governance decision. The canonical acceptance record is `docs/pilot/PILOT-05/PILOT05_C3_ACCEPTANCE_RECORD.json`. No open PILOT-05 blocker remains.

PILOT-04 C7 remains the historical PILOT-05 stage-entry pin, while accepted/frozen PILOT-04 C9 remains the later application-line alignment baseline. PILOT-05 acceptance does not automatically open PILOT-06, promote PILOT-07, claim production readiness/legal activation, or require immediate INTEGRATION-01 advancement. Further authoritative integration is governed by §2.1.

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

### PILOT-04 C9 authoritative transition — 2026-08-26

- **Previous state:** `DEVELOPED / NOT ACCEPTED_FROZEN`.
- **New state:** `PILOT-04 ACCEPTED / FROZEN`.
- **Governing candidate:** `EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C9.zip`.
- **Candidate SHA-256:** `7fc4f3a5a982d11535006fcea8201ffb694546a01f5326eaed09fcf4ffc78664`.
- **Candidate size:** `38,658,195` bytes.
- **Authoritative workflow:** `.github/workflows/pilot04-c9-accept.yml`, Git blob `59bdbffff589f23aa981d755d4d9ca628171f992`.
- **Authoritative run:** GitHub Actions `32601698352`, conclusion `success`, source head `5b49275818127ea7d4e3082ac1edc99c7a4d4755`, tested merge SHA `2504c2be709bad1189aeabc6ddd3058d27fad060`.
- **Authoritative evidence state:** `GITHUB_AUTHORITATIVE_PASS`; overall `PASS`; exit code `0`; all governed phases PASS.
- **Result digest:** `42163788bbeac04522d525cee99e254c1baef98d9d2b1f8fa8fe4692373c4a23`.
- **Mandatory property evidence:** A `29/29`, B `10/10`, C `8/8`, D `25/25`, E `PASS`, F `9/9`, G `494/494`.
- **Authoritative evidence artifact:** `pilot04-c9-authoritative-evidence`, artifact ID `9483475935`, artifact ZIP SHA-256 `5e7ac279069415fc7ff7007a59012f390ae16648abb46f25e8f0aebb63a4b3b4`.
- **Exact candidate artifact:** `pilot04-c9-exact-accepted-candidate`, artifact ID `9483476323`, artifact ZIP SHA-256 `8182abd5cf0f871475ab613f7e70b81ef5e3e1e2f2c17ed77004e5b75cb21cb0`.
- **Post-run freeze decision:** `docs/pilot/PILOT-04/PILOT04_C9_FROZEN_ACCEPTANCE_RECORD.json`, governance commit `49a1082fd3a46107b71deb4293308691bd1d306e`. The runner's `NOT_FROZEN` label was intentional self-acceptance prevention; this separate governance decision supplies the required freeze.
- **Open blockers for PILOT-04:** none.
- **Scope consequence:** PILOT-04 is frozen at C9; PILOT-05, PILOT-06, PILOT-07, production readiness, legal activation and integration acceptance are not promoted by this transition.
- **Next permitted primary program stage remains:** `API-02 — Authentication & Authorization Runtime`.

### PILOT-05 C3 authoritative transition — 2026-08-26

- **Previous state:** `C3 CANDIDATE / GOVERNANCE-STATIC PASS / FULL LIVE ACCEPTANCE NOT YET PROVEN`.
- **New state:** `PILOT-05 ACCEPTED / ESTABLISHED`.
- **Governing candidate:** `EPD2_PILOT05_REPRESENTATIVE_DESK_AND_TRANSPARENCY_PILOT_CANDIDATE_0.1_C3.zip`.
- **Candidate SHA-256:** `fc3f371bcf180e6559bc8ccc72cb74a88deef293f768424bcae7576731e8d8fb`.
- **Archive member count:** `3744`.
- **Authoritative workflow:** `PILOT-05 C3 terminal acceptance` (`.github/workflows/pilot05-c3-terminal.yml` at the authoritative run lineage; no current-repository workflow-blob identity is asserted by this reconciliation).
- **Authoritative run:** GitHub Actions `32855264419`, run attempt `1`, conclusion `success`, head SHA `126768f0ac66f809b93d96b215bc1b814592e364`.
- **Authoritative job:** `97825564426`, conclusion `success`.
- **Validator terminal result:** `PILOT05_C3_RESULT:PASS:/tmp/pilot05-c3-authoritative-evidence`.
- **Execution mode:** `FULL`; `static_only = false`; mandatory database/runtime prerequisites were present.
- **Live test evidence:** `3109 passed, 1 skipped, 0 failed`; mandatory execution PASS; F-01 adversarial `9/9 PASS`; F-02 unlinkability `8/8 PASS`; governance checks PASS.
- **Authoritative evidence artifact:** `pilot05-c3-authoritative-evidence-32855264419`, artifact ID `9578226563`, GitHub artifact digest `sha256:b36c48cc4c9ef27ab2adb64a3cda7a94b48824b6c2688fb3f5d1c9bae3e5af2d`.
- **Exact accepted candidate artifact:** `pilot05-c3-exact-accepted-candidate`, artifact ID `9578227300`, GitHub artifact digest `sha256:16194743369291fc0699640539283946822a56bca42f07c99eb02a8a76f731ee`.
- **Acceptance record:** `docs/pilot/PILOT-05/PILOT05_C3_ACCEPTANCE_RECORD.json`.
- **Historical environment blocker:** the earlier full-validator attempt without `EPD2_TEST_DATABASE_URL` is superseded by this successful full live run and is not an open blocker.
- **Open blockers for PILOT-05:** none.
- **Scope consequence:** PILOT-05 is accepted/established at C3; PILOT-06 and PILOT-07 are not automatically opened, and no production-readiness, legal-activation or integration-acceptance claim follows from this transition.
- **Next permitted primary program stage remains:** `API-02 — Authentication & Authorization Runtime`.

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

**Primary implementation:** `API-02 = ACTIVE / IN DEVELOPMENT` (`API-01 = ACCEPTED / CLOSED`). `API-03` may advance only as `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; exact accepted API-02 bytes must precede API-03 reconciliation/rebase, C1 seal and independent acceptance.

**Governed forward path:** complete active API-02 with independent authoritative acceptance; then reconcile/rebase API-03 to the exact accepted API-02 bytes, seal and independently verify API-03 before any acceptance/closure claim; then continue API-04 → API-05 → API-06 with independent authoritative acceptance at each stage; close API only after API-06. Then establish the explicit INFRA/OPS preview-readiness minimum and open `SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK`. The preview is an early usable-system checkpoint only and cannot close INFRA or OPS. After preview findings are handled through owning-layer lineage, complete INFRA → OPS → CTRL → FRONT, establish `FINAL INTEGRATION`, and run final SEC against that exact integrated baseline before the final readiness decision.

**Integration scheduling:** existing INTEGRATION-01 lineage is preserved, but no automatic new INTEGRATION-01 candidate is required after each API stage. Full authoritative integration is normally deferred until FRONT is closed; earlier targeted integration work is permitted only when a concrete compatibility blocker or acceptance dependency requires it.

**Parallel FRONT action:** FRONT-02 specification is established. The next legitimate FRONT-02 step is completion/acceptance of the mandatory specification artefacts named in `FRONT-02-SPECIFICATION.md`, followed by implementation within that scope. This does not change `API-02 = NEXT` and does not constitute FRONT acceptance or final closure.

**Parallel PILOT action:** PILOT-04 C9 is `ACCEPTED / FROZEN` and PILOT-05 C3 is `ACCEPTED / ESTABLISHED`; neither requires another acceptance rerun. PILOT-06 remains `NOT_STARTED_AS_GOVERNED_STAGE` until it is explicitly opened for governed pilot findings/corrections. Neither accepted PILOT stage changes `API-02 = NEXT`, claims production readiness/legal activation, or forces immediate INTEGRATION-01 advancement.

---

## 10. Mobile client execution decision — 2026-08-27

Governing execution record:

`docs/frontend/EPD2_MOBILE_CLIENT_EXECUTION_DECISION.md`

The following decision is now part of Program Control:

1. **MOBILE is not a new architecture layer.** Native iOS/Android clients are governed inside `FRONT` and do not alter the canonical sequence `DATA → API → INFRA → OPS → CTRL → FRONT → SEC`.
2. **MOBILE-READINESS specification may proceed before API closure** without changing the current primary stage. It may define mobile journeys, API-contract mapping, passkey/step-up UX, secure storage, device/session lifecycle, push/deep-link boundaries, offline behaviour, accessibility, privacy/telemetry boundaries, release/signing requirements and a web/mobile feature matrix. This work must not invent unaccepted API behaviour or claim runtime acceptance.
3. **Full mobile runtime implementation normally opens only after `API = CLOSED` and the first System Trial Preview has exercised the accepted API runtime sufficiently to stabilize client-facing assumptions.** Preview findings affecting client contracts must be reconciled by the owning layer first. The browser-first System Trial Preview is not blocked by the absence of native mobile.
4. The governed FRONT mobile sub-line is:
   - `FRONT-MOBILE-01 — Mobile Client Architecture & Security Boundaries`: `PLANNED / SPECIFICATION MAY PROCEED`;
   - `FRONT-MOBILE-02 — Mobile Application Runtime`: `NOT_STARTED`;
   - `FRONT-MOBILE-03 — Mobile E2E & Release Readiness`: `NOT_STARTED`.
5. Mobile remains a controlled client of accepted server-side authority. It may not access databases directly, own a separate AuthN/AuthZ domain, bypass Gateway/BFF/API boundaries, create a global user identifier, make authoritative domain/procedural decisions client-side, or move authoritative voting logic into the general mobile client. Human auth/session/assurance remains API-02-owned; S2S identity remains API-03-owned; WS-03 voting isolation and purpose-scoped handoff remain mandatory.
6. No framework is canonically locked now. `React Native + Expo` is the preferred candidate because the frontend line is TypeScript/React-oriented, but the choice must be verified and governed in FRONT-MOBILE-01.
7. Mobile feature parity is governed by an explicit feature matrix; complex administrative surfaces may remain web-only where justified. Required mobile journeys, optional journeys, prohibited mobile functions and safe cross-client handoffs must be explicit.
8. If native mobile is part of the target production release, FRONT cannot close merely because the web client is complete. The governed mobile target scope must be accepted before `FRONT CLOSED`, included in the exact `FINAL INTEGRATION` baseline and challenged by final `SEC` together with the rest of the integrated system.
9. **Master Register disposition:** no new FIR is created by this decision. Existing requirements already govern the substantive obligations, including `FIR-UX-003`, `FIR-UX-004` (explicit mobile navigation/deep-link scope), `FIR-UX-005`, `FIR-UX-006`, `FIR-ID-001`, `FIR-ID-002`, `FIR-INCLUSION-001` and existing privacy/security/voting-isolation requirements. If FRONT-MOBILE-01 discovers a genuinely new normative invariant not covered by the current Master, a new FIR ID must be created through normal Master change discipline before implementation relies on it.
10. This decision changes no current stage status. `API-02 = NEXT` remains the primary implementation position; FRONT-MOBILE-02 is not started, FRONT is not closed, and no mobile/production/security readiness is claimed.
