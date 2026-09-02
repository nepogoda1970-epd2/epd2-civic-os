# EPD² Program Control Register

**Status:** Living canonical execution-state register  
**Location:** `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`  
**Updated:** 2026-09-02  
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

Current Master maintenance level established by project governance work: **V26**, preserving the full accepted maintenance lineage and all legitimate V17–V24 governance additions, including `FIR-UX-012`, `FIR-UX-013`, `FIR-AI-003`, `FIR-GOV-004`, `FIR-GOV-005`, `FIR-SEC-004`, `FIR-TRUST-002`, `FIR-TRUST-003`, and `FIR-OSS-007`.

**Repository reconciliation note (superseded 2026-08-25, API-01 C3/C4 governance reconciliation):** the exact V16 repository reconciliation is **COMPLETED**. The Master Register inspected when this control register was introduced predated the V16 maintenance copy; that condition no longer holds. At that reconciliation point, the canonical Master Future Implementation Register was the reconciled repository Master (`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`, maintenance copy **V16**, sha256 `0a6a97a3ed04e78b7d925e750c2b99954b7e2c04b143f48ed28be7572b809c14`): the V15/V16 maintenance additions (`FIR-UX-012`, `FIR-UX-013`, update records carried as sections 1.66/1.67) are integrated into the newer repository history, no newer repository state was downgraded, and no V16-specific FIR state was inferred or reduced (record: `docs/api/API-01/API01_MASTER_REGISTER_RECONCILIATION.json`; this register's own transition: `docs/api/API-01/API01_PROGRAM_CONTROL_RECONCILIATION.json`). V16 reconciliation state: **COMPLETE**.

**Documentation-only V17 governance update (2026-08-27):** `FIR-AI-003 — Governed Correspondence Analysis & Reply Drafting` is now recorded in the canonical Master Future Implementation Register. Canonical Master SHA-256 after this update: `fe6b9c63088865ea1af4bce1fb8371c6abc6c0f21174c50ee52cce86c80b849a`. This update changes no execution-stage status, does not implement or activate the capability, and does not alter the primary position: **`API-02 = NEXT`**.

**Documentation-only V18 governance refinement (2026-08-27):** `FIR-AI-003` now contains a mandatory cross-layer Implementation Placement Matrix covering authoritative correspondence/casework ownership, AI processing, documents/evidence, API, INFRA, OPS, CTRL, FRONT, FINAL INTEGRATION and SEC. Canonical Master SHA-256 after this refinement: `5776d8bc49ad3b8c076a057d072c02abe7ad77203b5258ecf4770963ca6eba56`. No execution-stage status changes; **`API-02 = NEXT`** remains unchanged, and exact allocation among API-02…API-06 remains stage-contract governed.

**Documentation-only V19 governance update (2026-08-27):** `FIR-GOV-004 — Regional Authority Suspension & Intervention Control` is now recorded as an approved critical future requirement. It defines four bounded intervention levels — session quarantine, authority suspension, exact regional action restriction and narrow time-bounded temporary supervision — while prohibiting a universal `region_disabled` switch, implicit Bund takeover, voting-domain bypass and rewriting of historical evidence. Canonical Master SHA-256 after this update: `49d9be302bf027c6cda72805f67a9066d8dd5b7453ffab499b75ec1da34797ce`. This documentation update implements or activates no intervention capability and accepts/closes no implementation stage.

**Documentation-only V20 governance update (2026-08-28):** `FIR-SEC-004 — Governed Access, Credential & Key Authority Lifecycle Control` is now recorded as an approved critical future requirement. It separates human credentials, recovery, sessions, organizational authority, privileged JIT/break-glass, service credentials, platform cryptographic keys/provider secrets and voting-domain keys; defines separate request/approval/execution-custody/secret-visibility/review rights; and establishes planned rotation, emergency compromise, signing/trust-set, encryption-key, TLS/certificate, service-credential and human-recovery protocols. Canonical Master SHA-256 after this update: `11b2fd73824e045aac010b41025ffab58e5c7bb637b1e4e5505885dc58b91ae5`. This documentation update activates no key-management capability and accepts/closes no implementation stage. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; exact API-stage allocation remains stage-contract governed.

**Documentation-only V21 governance update (2026-08-28):** `FIR-GOV-005 — Statutory Party-Organ Competence & Digital Authority Binding` is now recorded as an approved critical future requirement. It binds future Civic OS `OrganizationalAuthority` to the exact adopted party-organ competence, rule version, source election/appointment/decision and scope; rejects hierarchy-based inherited administration; and records the governed party-organ competence model plus a non-adopted Satzung 0.3 amendment proposal covering regional autonomy, organs, territorial member assignment, intervention competence and digital authority binding. Canonical Master SHA-256 after this update: `e64a5388006e3f25f89b4d93a4e6a888a9227558df1fcb6eee90816560c07c01`. The technical/governance target is approved; the accompanying Satzung language is **NOT ADOPTED / NOT LEGALLY ACTIVATED** and requires competent party adoption after legal review. This documentation update accepts/closes no implementation stage. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; exact implementation placement remains stage-contract governed.

**Documentation-only V22 governance update (2026-08-28):** `FIR-TRUST-002 — Resilient Trust, Delegated Regional Issuance, Recovery & Immutable Audit` is now recorded as an approved critical future requirement. It establishes technology-neutral bounded regional trust/issuance, separates authoritative `OrganizationalAuthority` from short-lived signed runtime projections, prevents the central root/master key from becoming the hot path of ordinary regional work, defines Security containment deadlock boundaries, key-class-specific threshold custody, quorum-loss/root recovery ceremonies, explicit future RTO/RPO/autonomy targets and externally anchored immutable audit. It does not mandate DID, Keycloak, Vault, blockchain or a specific HSM/KMS provider. Canonical Master SHA-256 after this update: `124c326bd95cfb8821532479b530b306dd020983f873b3f0d924873bd4d0e6d5`. This documentation update implements/activates no trust provider and accepts/closes no implementation stage. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; exact implementation placement remains stage-contract governed.

**Documentation-only V23 governance update (2026-08-28):** `FIR-TRUST-003 — Cryptographic Key Classes, Algorithm Profiles & Crypto-Agility` is now recorded as an approved critical future requirement. The generic platform baseline fixes ES384/P-384 for root/intermediate/regional trust and high-impact audit signing; ES256/P-256 for short-lived authority/service JWS assertions; X.509/mTLS workload identity; WebAuthn ES256 as the mandatory offered passkey profile; AES-256-GCM application/envelope encryption; strict JOSE/JWKS key/algorithm/trust-location validation; class-specific cryptoperiod ceilings; and an inactive ML-KEM-768/ML-DSA-65 migration track. Concrete HSM/KMS/PKI provider selection remains INFRA-owned and PACK-16 voting cryptography is unchanged. Canonical Master SHA-256 after this update: `502ddd3ed8c3bf55e3847145772b0863ded01fdcd8521f4c3debf857d0cc0503`. API-02 remains `ACTIVE / IN DEVELOPMENT` and must reconcile with V23 before acceptance. API-03 remains `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; PRE-SEAL work may continue, but API-03 C1 seal is blocked until exact V23 S2S reconciliation on the exact independently accepted API-02 bytes. This documentation update implements/activates no provider and accepts/closes no implementation stage.

**Documentation-only V24 governance update (2026-08-29):** `FIR-OSS-007 — Open Trust Core & Commercial Operations Boundary` is now recorded as an approved critical future requirement. It fixes the boundary between a publicly inspectable trust core and commercial operational capabilities: verification-relevant protocol semantics, crypto/reference verification code, canonical encodings/test vectors, minimal reference voting client, independent verifier, guardian/key-ceremony protocol and evidence, election-record/finalization semantics and public audit-integrity verification remain open; managed hosting/orchestration, enterprise/admin/guardian UX, HA/resilience, HSM/KMS and government integrations, observability, compliance tooling, hardened/certified distributions, SLA/support and professional services may be commercial only where they are not required to establish cryptographic truth. `FIR-OSS-001` remains controlling: `EUPL-1.2` is unchanged as the intended original-project licence baseline subject to legal review; this update does not select Apache-2.0, relicense existing source or declare EUPL-covered code proprietary. Canonical Master SHA-256 after this update: `ac212cdd32c843a1403b069b51ea6e68a1f120ddadad414a50a0cbad35990e33`. PACK-15/16 voting isolation/cryptography remain unchanged. No execution-stage status changes; `API-02 = ACTIVE / IN DEVELOPMENT` and `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`.

**Governance reconciliation V25 (2026-08-29):** the canonical Master was losslessly reconciled upstream from current `main@007b5d71cf5a54e417cbd5647a35a57098ead186` and the independently reviewed accepted-maintenance/V23 union. The exact V25 Master SHA-256 is `895cf4186b88da74721f95d07ccdd6102a339a80d95ed19701e1695f5f7b4934`. The reconciliation preserves every FIR from both lineages, carries `FIR-OSS-007` from current main, and records `missing_after_merge = []` and `duplicate_active_ids = []` in `docs/roadmap/EPD2_MASTER_V25_RECONCILIATION.json`. No API, INFRA, OPS, CTRL, FRONT, SEC, PILOT or voting stage is accepted or closed by this repair. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; the V23 cryptographic profile and API-02/API-03 gates remain controlling.

**Documentation-only V26 BSI certification-readiness governance update (2026-08-30):** `FIR-VOTE-BSI-001 — BSI CC PP-0121 Certification Readiness` is recorded as an approved critical future requirement. The BSI/Common Criteria workstream is permitted only as **`PREPARATORY PARALLEL WORK / NOT CERTIFIED`**. It changes no DATA/API/INFRA/OPS/CTRL/FRONT/SEC/PILOT stage status, does not open SEC, and is not a BSI/CC conformance or certification claim. The mandatory readiness sequence is `ITSEF P0 feasibility → TOE boundary → Security Target → P1 closure → EAL4 + ALC_FLR.2 evidence → independent evaluation → BSI decision`. Until the written ITSEF P0 position exists, `no persistent member/person identifier inside voting domain` is a hard architectural freeze gate and may not be weakened merely for PP alignment. Internal party-election scope must not be assumed either in-scope or out-of-scope without written BSI/ITSEF classification. Governed matrix: `docs/security/bsi/EPD2_BSI_CC_PP_0121_CERTIFICATION_READINESS_GAP_MATRIX_0.1.md`.

**API-02 execution-state reconciliation (2026-08-27):** the project owner confirms that `API-02 — Authentication & Authorization Runtime` implementation is already underway. The current control state is therefore **`API-02 = ACTIVE / IN DEVELOPMENT`**, not `NEXT`. The existing `handoff/api-02` branch is intentionally reserved as a clean future candidate-verification/upload slot and is not the development branch, candidate evidence, PASS or acceptance record. Historical dated statements that API-02 was `NEXT` remain preserved as history and are superseded only for current-state interpretation. No API-02 PASS/ACCEPTED/CLOSED claim is made. `API-03` may proceed only as **`PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`** and may not be accepted or closed before authoritative API-02 acceptance.

**API-02 authoritative acceptance and closure (2026-09-01):** exact sealed candidate `EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C13.zip`, SHA-256 `9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9`, size `34,642,386` bytes, passed the independent GitHub Actions workflow `api02-accept`, authoritative run `33497989489`, job `99824485228`, provenance commit `ac76811912ab41772e75bd3fe366eb98bb2cddbd`, conclusion `success`. The run emitted `API02_RESULT:PASS:validation/api02/validator_result.json`; all `32/32` governed gates passed with no failed or environment-blocked gate. Exact live evidence includes PostgreSQL `16.15`, browser journey `41 passed / 1 skipped / 0 failed / 0 did_not_run`, `91` runtime-derived routes, `9` commit-time reauthorization refusal cases, `81` mutation fixtures, and stale-state audit `1437` hits / `0` unclassified. Step 27 bound the authoritative evidence to run `33497989489` and the exact candidate SHA. Authoritative evidence artifact `api02-c13-acceptance-evidence-33497989489`, artifact ID `9797383573`, GitHub artifact ZIP SHA-256 `ac5f940b98b58d18d1c7cde42314079bb1890bea3596cd5cad3997eeb1818f57`. The register-maintainer governance decision is recorded in `docs/api/API-02/API02_C13_ACCEPTANCE_RECORD.json`. **API-02 is therefore `ACCEPTED / CLOSED`.** The candidate's self-state `CANDIDATE_NOT_ACCEPTED` remains a valid no-self-acceptance safeguard in the sealed bytes and is superseded only by this independent post-run governance decision. The predecessor blocker on API-03 acceptance is released; API-03 is now the active primary API stage, must reconcile/rebase to these exact accepted C13 bytes before seal, and still requires its own independent acceptance. No API-03 acceptance/closure, API-layer closure, production-readiness, legal-activation, BSI/CC-certification or security-certification claim follows from this transition.


**API-03 authoritative acceptance and closure (2026-09-01):** exact resealed candidate `EPD2_API03_SERVICE_TO_SERVICE_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C5.zip`, SHA-256 `5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55`, size `43,300,451` bytes, passed the independent sealed GitHub Actions workflow `.github/workflows/api03-accept.yml`, authoritative run `33511256210`, job `99867183151`, provenance commit `412a6fb3e5445a92d3792ceecd17649e4afd132d`, conclusion `success`. The run emitted `API03_RESULT:PASS:validation/api03/authoritative_acceptance_result.json`; all `22/22` acceptance gates completed successfully with no failed or environment-blocked gate. Exact live evidence includes `99/99` API-03 tests with `0` failed and `0` skipped, PostgreSQL `16.15` / `server_version_num=160015`, workspace cryptography `46.0.7`, isolated offline cryptography `49.0.0`, governed R11 V23 PASS, real multi-process mTLS/replay topology PASS, and SEC-01 repository guard PASS. The first C5 seal SHA `8a62ea6c8ab1fb441811e476af0060f4b6c5374002312bb04e5a68968b6a3ea8` was correctly rejected by authoritative run `33510911890` because builder-side `py_compile` created an unaccounted verifier `.pyc` after seal verification; it is superseded by the corrected reseal above with runtime and sealed workflow unchanged. Authoritative evidence artifact `api03-c5-authoritative-acceptance-33511256210`, artifact ID `9801733668`, GitHub artifact digest `sha256:ccbf76b448ec634803330c0f5575a44bf50f50eae195cacfcfdfe53789987a78`. The governance decision is recorded in `docs/api/API-03/API03_C5_ACCEPTANCE_RECORD.json`. **API-03 is therefore `ACCEPTED / CLOSED`.** The candidate's self-state `CANDIDATE_NOT_ACCEPTED` remains the intentional no-self-acceptance safeguard in the sealed bytes and is superseded only by the independent post-run governance decision. No open API-03 blocker remains. `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` is now the next primary API stage. The API layer remains open until API-06; no production-readiness, legal-activation, final-security, BSI/CC or EAL4 certification claim follows from this transition.


**API-04 authoritative acceptance and closure (2026-09-02):** exact sealed candidate `EPD2_API04_EVENTS_AND_MESSAGING_RUNTIME_CANDIDATE_0.1_C1.zip`, SHA-256 `8356ba6f1b0e254f9aa215b4873a1e38f44a47fdac2ac859ff62bd95db999337`, size `43,880,523` bytes, passed the independent sealed GitHub Actions workflow `.github/workflows/api04-accept.yml`, authoritative run `33569092401`, job `100058880258`, provenance commit `299d4f4bce52daf14961e5d4cdb23c81ada05734`, conclusion `success`. The run emitted `API04_RESULT:PASS:validation/api04/authoritative_acceptance_result.json`; all `28/28` governed gates passed with no failed or environment-blocked gate. Exact live evidence includes `623/623` API-04 tests with `0` failed and `0` skipped, PostgreSQL `16.15`, RabbitMQ `3.12.1`, eight mTLS service principals, exact API-03 C5 predecessor binding, transactional outbox, durable inbox/deduplication, acknowledgement/crash/redelivery, schema compatibility, retry/DLQ/quarantine, replay/re-drive governance, asynchronous FIR-AUTH-001, voting isolation, API-chain non-regression, DATA no-new-regression, cross-service failure fixtures, mutation self-test and no API-05+ scope leakage all PASS. The independent runner also proved the exact C1 SHA/size, complete `SHA256SUMS` seal and byte-for-byte sealed acceptance workflow SHA-256 `3decc2dd0592800d7278ba83b3c6a88ed51177b78aa40b0966b62cac101e2bec`. Authoritative evidence artifact `api04-c1-authoritative-acceptance-33569092401`, artifact ID `9824542224`, GitHub artifact digest `sha256:0289b930353f74a7e263af3c55df24b0ebf8578e45238b6b56a2bfd90193109f`. The governance decision is recorded in `docs/api/API-04/API04_C1_ACCEPTANCE_RECORD.json`. **API-04 is therefore `ACCEPTED / CLOSED`.** The candidate's `CANDIDATE_NOT_ACCEPTED` self-state remains the intentional no-self-acceptance safeguard and is superseded only by the independent post-run governance decision. No open API-04 blocker remains. `API-05 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` is now the next primary API stage. The API layer remains open until API-06; no production-readiness, legal-activation, final-security, BSI/CC or EAL4 certification claim follows from this transition.


**API-05 authoritative acceptance and closure (2026-09-02):** exact sealed candidate `EPD2_API05_EXTERNAL_INTEGRATION_BOUNDARY_CANDIDATE_0.1_C1.zip`, SHA-256 `38bab7663b54f9f81538666315ee16195b0aa086e5b5c50c2b87acc3f4f03a70`, size `43,953,160` bytes, passed the independent sealed GitHub Actions workflow `.github/workflows/api05-accept.yml`, authoritative run `33574342011`, job `100074902089`, provenance commit `23fb2c034959cc74a006df89d377c5669e2e0398`, conclusion `success`. The run emitted `API05_RESULT:PASS:validation/api05/authoritative_acceptance_result.json`; all `8/8` governed gates passed with no failed or environment-blocked gate. Exact live evidence includes `66/66` API-05 behavioral tests with `0` failed, PostgreSQL `16.15` (`server_version_num=160015`) with the PostgreSQL gate passing, locked dependency provisioning, Ruff check/format, clean archive hygiene, exact accepted API-04 C1 predecessor binding with `4,237` predecessor files verified unchanged, complete `SHA256SUMS` seal and byte-for-byte equality of the installed acceptance workflow with sealed workflow SHA-256 `6b2fba5dba895594ac246547ace3b62074b9a80f3c76b3fc3e4a88da8173e106`. The accepted C1 contains the independently hardened external-integration boundary for pinned DNS-to-connection dispatch, query-bound endpoint allowlisting, recursive identifier isolation, semantic validation before replay reservation, idempotent callback publication recovery, retry-time reauthorization and predecessor dependency-version preservation. Authoritative evidence artifact `api05-c1-authoritative-acceptance-33574342011`, artifact ID `9826088503`, GitHub artifact digest `sha256:251f429765b86687a3064fa6a7b45bac7b8cca8dfbb11c5aca79c0fec868ec78`. The governance decision is recorded in `docs/api/API-05/API05_C1_ACCEPTANCE_RECORD.json`. **API-05 is therefore `ACCEPTED / CLOSED`.** The candidate's `CANDIDATE_NOT_ACCEPTED` self-state remains the intentional no-self-acceptance safeguard and is superseded only by the independent post-run governance decision. No open API-05 blocker remains. `API-06 = NEXT`; it is not marked active because no canonical API-06 stage/handoff is present on `main` at this transition. The API layer remains open until API-06 receives its own authoritative acceptance; no production-readiness, legal-activation, final-security, BSI/CC or EAL4 certification claim follows from this transition.


**FRONT-03 authoritative acceptance and bounded stage closure (2026-09-01):** exact sealed candidate `EPD2_FRONT03_WS02_APPLICANT_AND_MEMBER_CORE_CANDIDATE_0.1_C1.zip`, SHA-256 `fec7b19d77c27cbc3ef8a34e433f5aef94ef7853f76d3212bed6acd682497c26`, size `17,646,011` bytes, passed independent sealed-byte GitHub verification in workflow `FRONT-03 C1 governed finalize`, authoritative acceptance run `33528038712`, job `99923795567`, workflow commit `8fb650b5b82611926664474b93f6155d4c70d2de`, conclusion `success`. The independent runner downloaded the already sealed C1 artifact, verified exact SHA/size/CRC and no-self-acceptance state, performed a fresh locked dependency install, formatting/type/lint/unit/build verification, and reproduced the governed browser/visual/security boundary evidence: TAP `58/58 PASS`, Vitest `30/30 PASS`, inherited nonvisual browser regression `195/195 PASS`, exact API-02 production browser `12/12 PASS`, production fail-closed browser `6/6 PASS`, immutable FRONT-03 visual baseline `27/27 PASS`, C1 validator `14/14 PASS`, and C1 mutation resistance `9/9 DETECTED`. The run emitted `FRONT03_C1_ACCEPTANCE_RESULT:PASS:fec7b19d77c27cbc3ef8a34e433f5aef94ef7853f76d3212bed6acd682497c26:17646011`. Authoritative evidence artifact `front03-c1-acceptance-evidence-33528038712`, artifact ID `9808685208`, GitHub artifact digest `sha256:27dad0fb37c18bdeeda2d7d2b3670f5d0972a320b2956c8038dfe888f993e152`. Exact lineage is accepted FRONT-02 C2.1 SHA-256 `aaf980a2cd3b3b06d48218adaa68d109c8770e6abfcbef230197b51a87006179` + FRONT-03 PRESEAL SHA-256 `da356d58192fa3afd5cedf0c7d8423df1faac3dd915d5ba26884dcb79e366294` + exact accepted API-02 C13 SHA-256 `9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9`; no real API-03 S2S dependency was discovered for the C1 browser-to-API-02 binding, so none was invented. Voting/BSI readiness evidence preserves the hard freeze against persistent member/person identity in the voting domain and introduces no unrecorded certification blocker; all BSI/CC claims remain expressly excluded. Governance decision is recorded in `docs/frontend/FRONT-03-C1-ACCEPTANCE-RECORD.json`. **FRONT-03 C1 is therefore `ACCEPTED / CLOSED` as a bounded WS-02 implementation stage.** This does not close the entire FRONT layer, does not alter the canonical primary program stage, and does not declare production readiness, legal activation, BSI/CC/EAL4 certification, or final security acceptance.

**FRONT-04 authoritative acceptance and bounded stage closure (2026-09-01):** exact corrected sealed candidate `EPD2_FRONT04_WS03_VOTING_CLIENT_CANDIDATE_0.1_C2.zip`, SHA-256 `1ac87914a30e589b4059e3b7c74e0a0fd940a78cecbe7f06de299421c8da55f8`, size `21,448,756` bytes, passed the exact-byte GitHub Actions workflow `.github/workflows/front04-c2-authoritative-accept.yml`, authoritative run `33569268417`, job `100059427183`, reviewed commit `66a65f2303d2a0d18fb8396887a35d6c14df1d92`, conclusion `success`. The run independently pinned candidate SHA/size and detached sidecar, verified clean archive hygiene (`1693` entries, `0` duplicates/traversal/symlinks/runtime contamination), reconciled the corrected report identity to source-tree digest `eee6bf1e80f9e5b5ce18618611513b871b195a163e98948d55d99f61276f2f2e`, reproduced all `29/29` FRONT-04 gates, detected all `32/32` governed mutations, rejected all `6/6` independent stale-evidence attacks, and passed the BSI voting hard-freeze gate including validator `F418`. The terminal marker is `FRONT04_C2_AUTHORITATIVE_RESULT:PASS:1ac87914a30e589b4059e3b7c74e0a0fd940a78cecbe7f06de299421c8da55f8:21448756`. Authoritative evidence artifact `front04-c2-authoritative-acceptance-33569268417`, artifact ID `9824319414`, artifact ZIP SHA-256 `83ac65e0d72686fcabad7314f040d445d3543e0621bf9bf2db408e8fcb05aec2`; repaired independent corroboration run `33569270616`, job `100059434289`, also concluded `success`. The earlier C2 SHA `04d71eaed46bd4278f742823b244ff42fe5fa55be16b7688ae2029c5231e3a98` was never accepted and is superseded by the corrected reseal; reseal run `33568939594`, job `100058414374`, resulting commit `bbe05f28f354f21725805b0b7b1c223114c0bd42`. The candidate's `CANDIDATE_NOT_ACCEPTED` self-state remains the intentional no-self-acceptance safeguard and is superseded only by this post-run governance record. Stage contract `1.0.0`, digest `b5bfab8f8d74cfe0028a435a6bfbf94d116ff232781c55b5f72532caded76cc2`, is ratified for this bounded C2 acceptance. Governance decision is recorded in `docs/frontend/FRONT-04-C2-ACCEPTANCE-RECORD.json`. **FRONT-04 C2 is therefore `ACCEPTED / CLOSED` as the bounded WS-03 Voting Client stage.** This accepts only the WS-03 frontend, voting-client isolation and fail-closed boundary. It does **not** accept a complete executable production voting system or voting cryptography, does not legally activate binding digital voting, does not claim BSI/Common Criteria/EAL4 certification, production readiness or final security acceptance, does not close the entire FRONT layer, and does not alter the canonical primary program stage.

**INFRA-01 authoritative acceptance and bounded stage closure (2026-09-01):** exact corrected C3 candidate `EPD2_INFRA01_CI_ACCEPTANCE_HARNESS_CANDIDATE_0.1_C3.zip`, SHA-256 `5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131`, size `15,854,311` bytes, passed the full independent GitHub Actions workflow `INFRA-01 C3 Authoritative Review`, authoritative run `33556094346`, job `100017170812`, workflow commit `9537d6624b446a78d6646c0d5508860907f83b3f`, conclusion `success`. All `43/43` governed checks executed and passed with `0` FAIL and `0` BLOCKED, including governance freshness, full backend/security suites, Prettier/type/lint/tests, Next build, browser, accessibility, visual, secrets, freeze, byte-identical packaging and independent evidence reconciliation. The exact source commit is `38f7d13c8badf911e61d659adb2905d1089a64a5`, freeze tree digest `d022822dbf3a127919595848cc7688053b2601210c56fa9d01aed54172fd4db6`, and the terminal marker is `INFRA01_C3_AUTHORITATIVE_RESULT:PASS`. Authoritative evidence artifact `infra01-c3-authoritative-evidence-33556094346`, artifact ID `9819611454`, GitHub artifact digest `sha256:eb0997a9c5de08c21d3efd34a64de987a1b984258947e7d95d59bd0bb37c868e`; exact candidate artifact `infra01-c3-authoritative-candidate-33556094346`, artifact ID `9819612258`, GitHub artifact digest `sha256:78776108bbf045fb20ad9cc9e395b6954aa81fa3b19baefb23863c35c9bfd1a3`. The earlier authoritative run `33541200112` correctly failed only `frontend.prettier`; the four diagnosed formatting defects were corrected without weakening any runtime, security, registry, test or harness semantics, and the complete authoritative suite was rerun from the corrected exact source. The governance decision is recorded in `docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json`. **INFRA-01 is therefore `ACCEPTED / CLOSED` as a bounded infrastructure-foundation stage.** The overall INFRA layer remains open and its final closure still follows the canonical API dependencies. `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` remains unchanged. No production-readiness, legal-activation, BSI/CC/EAL4 or final-security claim follows from this transition.

**INFRA-02 authoritative acceptance and bounded stage closure (2026-09-02):** exact sealed candidate `EPD2_INFRA02_CI_CD_AND_SOFTWARE_SUPPLY_CHAIN_CANDIDATE_0.1.zip`, SHA-256 `d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c`, size `15,980,332` bytes, passed independent exact-byte GitHub Actions authoritative review, run `33574647511`, job `100075828121`, conclusion `success`. Independent review proved exact transport identity, clean seal/freeze hygiene, exact accepted INFRA-01 C3 predecessor SHA-256 `5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131`, predecessor delta `35 added / 11 modified / 0 removed / 1450 unchanged`, governance freshness, `146/146` targeted tests, and full canonical harness `51/51 PASS`. Current-run evidence returned `INFRA01_EVIDENCE_RESULT:PASS`; submitted candidate and harness-produced package were independently bound by `INFRA02_PACKAGE_CONTENT_IDENTITY:PASS:1496`; terminal marker `INFRA02_AUTHORITATIVE_RESULT:PASS:d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c:15980332`. Post-run reconciliation against `main@4b95cc952897bd78fe912a2737f53e66264d6ff1` classified the concurrent API-05 PCR closure and formatting-only API-05 helper change as `NO_INFRA02_CONTROLLING_CONFLICT`; newer `API-05 ACCEPTED / CLOSED; API-06 NEXT` state is preserved. The governance decision is recorded in `docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json`. **INFRA-02 is therefore `ACCEPTED / CLOSED` as the bounded CI/CD & Software Supply-Chain Integrity stage.** The overall INFRA layer remains open; INFRA-03…INFRA-07 are not promoted. No production-readiness, hosting-provider, legal-activation, BSI/CC/EAL4 or final-security claim follows.

**OPS-01 authoritative acceptance and bounded stage closure (2026-09-01):** exact sealed C2 candidate `EPD2_OPS01_OPERATIONAL_READINESS_INCIDENT_RECOVERY_AND_CHANGE_CONTROL_CANDIDATE_0.1_C2.zip`, SHA-256 `39a6b02af03269a8ebf61216503fa03df2abf4e5194aa3c45c6f4bb176f2ad27`, size `16,457,357` bytes, passed the independent sealed-byte GitHub Actions workflow `OPS-01 C2 Authoritative Review`, authoritative run `33564968274`, job `100045926256`, workflow commit `0cb18e707d18d034d8dec8d76662f3aac8042eca`, conclusion `success`. The runner independently proved ZIP structure and exact transport identity, bound the candidate byte-for-byte to canonical authority `main@e89778667ee65e38001874b01681eff64c11354f`, verified all `1,486` governed freeze-manifest files and freeze tree digest `e08ef203c096e17779592407d7b48c843c84f4f27d99e6e7514ddb7491a11613`, executed the locked environment on PostgreSQL `16.15`, passed Ruff format/check and mypy, passed `88/88` OPS tests, and completed all `32/32` OPS-01 gates with `0` failed, `0` skipped, `0` environment-blocked and `0` not-run. The exact terminal marker is `OPS01_C2_AUTHORITATIVE_RESULT:PASS:39a6b02af03269a8ebf61216503fa03df2abf4e5194aa3c45c6f4bb176f2ad27`; same-governed-source-byte verification also passed after execution. Authoritative evidence artifact `ops01-c2-authoritative-evidence-33564968274`, artifact ID `9822755955`, GitHub artifact digest `sha256:4bc58f043f0a89753086a5d6b560bf7af800e80cc310ec5951c60035ad6567f7`; exact reviewed-candidate artifact `ops01-c2-authoritative-candidate-33564968274`, artifact ID `9822756668`, GitHub artifact-wrapper digest `sha256:8e07a54a1a5b60285485e595630cca060a7c6c05f12c88d89b3dc97b45c22a46`. Before recording the post-run decision, governance fail-closed reconciled the newer canonical `main@f568ca2538d0a3ea83825c8eb6f229bebf4c438a` against the authoritative target: all controlling PCR/Master/BSI/INFRA/PACK-15/PACK-16 authority files remained unchanged; `2` concurrent non-authority file change(s) were recorded in the acceptance record with classification `NO_CONTROLLING_AUTHORITY_CONFLICT`. The independent BSI certification-readiness disposition is `PASS_WITH_EXPLICIT_EXISTING_DEFERRED_GAPS`: touched rows `M-02`, `M-03`, `M-11`, `M-16`, `M-17`, `M-19`, `M-20`, `M-25`, `M-27`, `M-30`; `new_certification_blockers = []`; stronger EPD² voting unlinkability/no-persistent-identifier invariants are preserved, and nine existing certification gaps remain explicitly deferred with owner, closure stage and required evidence in `docs/ops/OPS-01/OPS01_C2_BSI_READINESS_DISPOSITION.json`. The governance decision is recorded in `docs/ops/OPS-01/OPS01_C2_ACCEPTANCE_RECORD.json`. **OPS-01 is therefore `ACCEPTED / CLOSED` as a bounded operational-foundation stage.** The overall OPS layer remains open and its final closure still follows the canonical API/INFRA dependencies. `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` remains unchanged. No production-readiness, legal-activation, BSI/CC/EAL4 or final-security claim follows from this transition.

On 2026-08-26 API-01 completed independent authoritative acceptance. Exact candidate `EPD2_API01_PRODUCTION_API_GATEWAY_AND_BFF_BOUNDARIES_CANDIDATE_0.1_C5.zip`, sha256 `cea2fb0e23ee174e802ec1899cf62e570e5c8659a0f31c7e6c3c3955bffa3d27`, passed GitHub Actions workflow `api01-accept`, authoritative run `32967210855`, conclusion `success`. API-01 is therefore `ACCEPTED / CLOSED`; API-02 is the next permitted primary API stage.

On 2026-08-26 the previously stale PILOT-05 control state was reconciled to its already-completed full live authoritative evidence: exact C3 sha256 `fc3f371bcf180e6559bc8ccc72cb74a88deef293f768424bcae7576731e8d8fb` passed GitHub Actions run `32855264419`, conclusion `success`, with `3109 passed, 1 skipped, 0 failed`, F-01 `9/9 PASS` and F-02 `8/8 PASS`. PILOT-05 is therefore `ACCEPTED / ESTABLISHED`; this does not alter `API-02 = NEXT`.

---


**OPS-02 authoritative acceptance and bounded closure (2026-09-02):** exact sealed candidate `EPD2_OPS02_PREVIEW_OPERATIONS_DEPLOYMENT_OBSERVABILITY_AND_RECOVERY_CANDIDATE_0.1_C3.zip`, SHA-256 `ac3b543b0cb3a8e45f7d973c841769d0b4c6e7af649a54aee034f3e0b6afc125`, size `16,632,939` bytes, passed independent sealed-byte workflow `.github/workflows/ops02-c3-authoritative-v3.yml`, authoritative run `33610516469`, job `100184288996`, conclusion `success`. The run independently verified exact transport and source-bundle provenance, canonical-authority binding, metadata/freeze integrity, locked dependencies, PostgreSQL `16.15`, Ruff/mypy, `57/57` OPS-02 runtime tests, all `42/42` governed gates with no failed/missing/skipped/environment-blocked/not-run/manual-assume-pass gate, privacy-safe observability and voting-isolation controls, BSI disposition `PASS_WITH_EXPLICIT_EXISTING_DEFERRED_GAPS`, and the same governed source bytes after live execution. Authoritative evidence artifact `ops02-c3-authoritative-v3-evidence-33610516469`, artifact ID `9838829213`, digest `sha256:91a178f2f255db7761d49d86f0d0384aa2326b2a56981332ed44c0efb0124f93`; exact candidate artifact ID `9838830658`, digest `sha256:2d9cd097e5844395ac18f59d76d1fdd98c72f2e5ebab23c7abf52314a093647e`. The sealed candidate correctly retains `CANDIDATE_NOT_ACCEPTED`; that no-self-acceptance state is superseded only for this bounded stage by `docs/ops/OPS-02/OPS02_C3_ACCEPTANCE_RECORD.json`. **OPS-02 is therefore `ACCEPTED / CLOSED` as a bounded stage.** The overall OPS layer remains **OPEN**. Candidate preview status remains `TECHNICALLY_READY_BUT_BLOCKED_BY_API`; API-06/API-layer governance prerequisites are not waived and System Trial Preview is **NOT OPENED**. No production-readiness, legal-activation, BSI/CC/EAL4 or final security claim follows.


**CTRL-01 authoritative acceptance and bounded stage closure (2026-09-02):** exact sealed candidate `EPD2_CTRL01_GOVERNED_CONTROL_PLANE_CANDIDATE_0.1_C1.zip`, SHA-256 `07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5`, size `190,099` bytes, passed independent exact-byte GitHub Actions review in `.github/workflows/ctrl01-c1-canonical.yml`, authoritative run `33618683269`, build job `100210392348`, authoritative job `100210596079`, workflow commit `246824a099fd1e7359e79650a7107d7cfa8ddb43`, conclusion `success`. The independent replay verified the complete internal SHA-256 seal, locked dependencies, Ruff, mypy, `178/178` runtime tests, all `22/22` governed CTRL gates, `37/37` mutation attacks detected, and `43` commit-time reauthorization mutations. Terminal marker: `CTRL01_C1_AUTHORITATIVE_RESULT:PASS:07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5:190099`. The canonical promotion installs the exact sealed C1 payload bytes under `docs/ctrl/CTRL-01`, `scripts`, `services/control-plane-service` and `validation`, and records their hashes in `docs/ctrl/CTRL-01/CTRL01_C1_CANONICAL_INSTALLATION_MANIFEST.json`. The sealed candidate correctly retained `CANDIDATE_NOT_ACCEPTED`; that no-self-acceptance state is superseded only for this bounded module by `docs/ctrl/CTRL-01/CTRL01_C1_ACCEPTANCE_RECORD.json`. **CTRL-01 C1 is therefore `ACCEPTED / CLOSED` as a bounded Governed Control Plane stage.** The overall CTRL layer remains **OPEN / NOT CLOSED**. `API-06` remains `NEXT / NOT ACCEPTED`; the API layer remains open and System Trial Preview remains **CHECKPOINT_NOT_OPEN**. No production-readiness, legal-activation, BSI/Common Criteria/EAL4 or final-security claim follows.


**API-06 authoritative acceptance, terminal API-stage closure and API-layer closure (2026-09-02):** exact sealed candidate `EPD2_API06_API_LAYER_COMPLETION_AND_PREVIEW_READINESS_CANDIDATE_0.1_C1.zip`, SHA-256 `3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c`, size `44,012,716` bytes, passed independent exact-byte GitHub Actions authoritative review, run `33629147572`, job `100243984921`, provenance commit `2f3f951baa9d392ff7b0decc1137bcc0670c8fd2`, conclusion `success`. The independent runner verified exact candidate identity and complete internal SHA-256 seal, byte-for-byte sealed acceptance-workflow equality, current canonical API-05 closure/API-06 entering governance, locked dependencies, accepted API-04 live regression environment, all `40/40` governed API-06 gates, `30/30` mutations detected, PostgreSQL `16.15`, and unchanged sealed source after execution. Terminal marker: `API06_RESULT:PASS:validation/api06/external_authoritative_result.json`. Authoritative evidence artifact `api06-c1-authoritative-acceptance-33629147572`, artifact ID `9846196028`, digest `sha256:b1c4bb5072a8040b2eaa52a5f31bdfe353b6841228c18e9cd456122d6578bc8c`. The governance decision is recorded in `docs/api/API-06/API06_C1_ACCEPTANCE_RECORD.json`, and the exact sealed API-06 payload is installed in canonical `main` with hashes in `docs/api/API-06/API06_C1_CANONICAL_INSTALLATION_MANIFEST.json`. **API-06 is therefore `ACCEPTED / CLOSED`, and the API layer is `CLOSED`.** The sealed candidate's `CANDIDATE_NOT_ACCEPTED` self-state remains the intentional no-self-acceptance safeguard and is superseded only by the independent run plus this post-run Project Owner decision. This releases the API dependency for INFRA/OPS preview-readiness qualification, but does **not** automatically open System Trial Preview, close INFRA/OPS, claim production readiness, legal activation, BSI/CC/EAL4 certification or final security acceptance.

## 2. Program phase state

| Program layer | Current control state | Execution rule |
| --- | --- | --- |
| ARCH PACK-01…35 | `CLOSED` | Do not restart architecture PACK sequencing as current work. |
| DATA | `CLOSED` | Do not describe DATA as still being finished unless a governed correction explicitly reopens it. |
| API | `API-01 ACCEPTED / CLOSED; API-02 ACCEPTED / CLOSED; API-03 ACCEPTED / CLOSED; API-04 ACCEPTED / CLOSED; API-05 ACCEPTED / CLOSED; API-06 ACCEPTED / CLOSED; API LAYER CLOSED` | Exact API-06 C1 is independently accepted and its exact sealed payload is installed in canonical main. The API layer is CLOSED. This releases the API prerequisite for INFRA/OPS preview-readiness qualification; System Trial Preview still requires an explicit checkpoint-opening decision and does not close INFRA or OPS. |
| INFRA | `INFRA-01 ACCEPTED / CLOSED; INFRA-02 ACCEPTED / CLOSED; INFRA LAYER OPEN` | Exact bounded INFRA-01 C3 and INFRA-02 software supply-chain foundation are accepted/closed. The overall INFRA layer remains open; INFRA-03…INFRA-07 and final INFRA closure remain governed separately and still follow API dependencies. |
| OPS | `OPS-01 ACCEPTED / CLOSED; OPS-02 ACCEPTED / CLOSED; OPS LAYER OPEN; OPS-03 QUALIFICATION ELIGIBLE` | Exact bounded OPS-01 C2 and OPS-02 C3 are accepted/closed. API-06/API-layer closure has released the final-API-runtime prerequisite for OPS-03 qualification. The overall OPS layer remains open; OPS-03 still requires its own exact candidate, governed PASS and independent acceptance, and System Trial Preview is not opened by this API transition. |
| CTRL | `CTRL-01 ACCEPTED / CLOSED; CTRL LAYER OPEN` | Exact bounded CTRL-01 C1 Governed Control Plane is accepted/closed and its exact sealed payload is installed in canonical main. The overall CTRL layer remains open. API-06/API are now closed, but System Trial Preview remains separately checkpoint-governed and later CTRL work/whole-layer closure remain separately governed. |
| FRONT | `FRONT-02 C2.1 ACCEPTED_IMPLEMENTATION_BASELINE; FRONT-03 C1 ACCEPTED / CLOSED; FRONT-04 C2 ACCEPTED / CLOSED; NOT_STARTED_FINAL` | Exact FRONT-02 C2.1, bounded FRONT-03 C1, and bounded FRONT-04 C2 are accepted governed frontend baselines. The overall FRONT layer remains open; final integrated journeys and FRONT-layer closure remain dependent on API → INFRA → OPS → CTRL. |
| SEC | `NOT_STARTED_FINAL` | Threat/adversarial preparation may proceed; final challenge targets the integrated system. |
| BSI / CC readiness | `PREPARATORY PARALLEL WORK / NOT CERTIFIED` | P0 feasibility, TOE/ST preparation and assurance planning may proceed in parallel. This opens no SEC stage, changes no implementation-stage status and creates no certification claim. Hard P0 identity freeze applies. |
| PILOT | `PARALLEL_DEVELOPMENT_EXISTS` | PILOT-01…05 have existing lineage/work. Exact stage state is governed below. |

Canonical primary closure sequence:

```text
DATA → API → INFRA → OPS → CTRL → FRONT → SEC
```

Current primary position:

```text
DATA = CLOSED
API-01 = ACCEPTED / CLOSED
API-02 = ACCEPTED / CLOSED
API-03 = ACCEPTED / CLOSED
API-04 = ACCEPTED / CLOSED
API-05 = ACCEPTED / CLOSED
API-06 = ACCEPTED / CLOSED
API = CLOSED
NEXT CHECKPOINT = INFRA/OPS PREVIEW-READINESS MINIMUM
```

### 2.1 Governed execution path with intermediate system trial

The canonical layer order above is unchanged. The following checkpoint-aware execution path governs how the remaining work is to be exposed as a usable system while preserving independent layer acceptance:

```text
DATA CLOSED
  → API-01 CLOSED
  → API-02 CLOSED
  → API-03 CLOSED
  → API-04 CLOSED
  → API-05 CLOSED
  → API-06 CLOSED
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

With `API = CLOSED`, parallel work may continue while the explicit INFRA/OPS preview-readiness minimum is qualified. API-06 is accepted/closed at exact C1; no parallel line may treat API closure as automatic INFRA/OPS/CTRL/FRONT closure or as System Trial Preview opening:

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

### FRONT-02 C2.1 authoritative acceptance transition — 2026-08-29

- **Previous state:** `FRONT-02_SPECIFIED / NOT_STARTED_FINAL`.
- **New state:** `FRONT-02 C2.1 ACCEPTED_IMPLEMENTATION_BASELINE / NOT_STARTED_FINAL`.
- **Governing candidate:** `EPD2_FRONT02_IMPLEMENTATION_CANDIDATE_0.1_C2.1_2026-08-30.zip`.
- **Candidate SHA-256:** `aaf980a2cd3b3b06d48218adaa68d109c8770e6abfcbef230197b51a87006179`.
- **Independent authoritative review:** GitHub Actions `front02-governed-review`, run `33280335794`, conclusion `success`; exact-byte verification, safe extraction, clean dependency install, catalogue validation, formatting, typecheck, lint, unit tests, FRONT-02 browser gates, FRONT-00 visual regression and FRONT-01 browser regression all passed.
- **Acceptance decision:** Project Owner decision recorded in `docs/frontend/FRONT-02-C2.1-ACCEPTANCE-RECORD.json`.
- **Final-closure predecessor status:** ARCH and DATA are closed; API remains active, and INFRA, OPS and CTRL are not started. These do not invalidate this bounded implementation-baseline acceptance; they prevent `FRONT CLOSED`.
- **Open blockers for this acceptance:** none.
- **Next permitted primary stage:** unchanged — `API-02 = ACTIVE / IN DEVELOPMENT`.

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

### API-02 C13 authoritative transition — 2026-09-01

- **Previous state:** `API-02 ACTIVE / IN DEVELOPMENT`; sealed candidate self-state `CANDIDATE_NOT_ACCEPTED`.
- **New state:** `API-02 ACCEPTED / CLOSED`.
- **Governing candidate:** `EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C13.zip`.
- **Candidate SHA-256:** `9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9`.
- **Candidate size:** `34,642,386` bytes.
- **Builder evidence:** GitHub Actions run `33495990810`, conclusion `success`, builder head `a378ac688e550de6907b7f8ea8ef19851837c1de`; C13 sealing converged with `3953` files and zero runtime-delta paths from C12.
- **Authoritative workflow:** `.github/workflows/api02-accept.yml`, exact sealed workflow Git blob `55bcb7571d60eaaaf9c11f15f35c2a27d3961ee9`, workflow SHA-256 `9c93f870deaa8b6da4c74f9baa958285043d35adc19c5989cf42fe0a56f3292b`.
- **Authoritative run:** GitHub Actions `33497989489`, run attempt `1`, job `99824485228`, conclusion `success`, provenance commit `ac76811912ab41772e75bd3fe366eb98bb2cddbd`.
- **Validator terminal result:** `API02_RESULT:PASS:validation/api02/validator_result.json`; all `32/32` gates PASS, no failed or environment-blocked gate.
- **Live environment:** PostgreSQL `16.15`; 10/10 constraint-violation probes refused; frozen Chromium provisioning fail-closed; browser journey `41 passed, 1 skipped, 0 failed, 0 did_not_run`.
- **Security/runtime assertions:** `9` commit-time reauthorization refusal cases; voting isolation, privileged separation and recovery groups PASS; `91` routes derived from runtime source and fully classified; `81` mutation fixtures; candidate identity C13; consistency state exact; stale audit `1437` hits / `0` unclassified.
- **Authoritative evidence binding:** step 27 proved the published evidence was written by run `33497989489` for candidate SHA `9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9`.
- **Authoritative evidence artifact:** `api02-c13-acceptance-evidence-33497989489`, artifact ID `9797383573`, artifact size `782,435` bytes, GitHub artifact ZIP SHA-256 `ac5f940b98b58d18d1c7cde42314079bb1890bea3596cd5cad3997eeb1818f57`.
- **Acceptance decision:** register-maintainer decision recorded in `docs/api/API-02/API02_C13_ACCEPTANCE_RECORD.json`.
- **Open blockers for API-02:** none.
- **Scope consequence:** API-02 is closed at exact C13. This transition does not accept/close API-03, does not close the API layer, and makes no production-readiness, legal-activation, security-certification or BSI/CC-certification claim.
- **Next permitted primary stage:** `API-03 — Service-to-Service Authentication & Authorization Runtime`, `ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`; reconcile/rebase to exact accepted API-02 C13 before seal and independent acceptance.

### API-03 C5 authoritative transition — 2026-09-01

- **Previous state:** `API-03 ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`; sealed candidate self-state `CANDIDATE_NOT_ACCEPTED`.
- **New state:** `API-03 ACCEPTED / CLOSED`.
- **Governing candidate:** `EPD2_API03_SERVICE_TO_SERVICE_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C5.zip`.
- **Candidate SHA-256:** `5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55`.
- **Candidate size:** `43,300,451` bytes.
- **Corrected seal/reseal builder:** run `33511140504`, provenance commit `9d4292eb38a388c85ac0205a02c47d4a525ddcb1`, artifact ID `9801661733`, outer digest `sha256:b85551b811c0a75358b9f5c717830a5a3306b82d473fd6c49e0c0a9e6373d0e3`; complete seal accounting covers `4125` files.
- **Superseded failed seal:** SHA-256 `8a62ea6c8ab1fb441811e476af0060f4b6c5374002312bb04e5a68968b6a3ea8`, builder run `33510681168`, rejected by authoritative run `33510911890` because `py_compile` created unaccounted `scripts/__pycache__/api03_verify_seal.cpython-312.pyc` after successful pre-package seal verification. Corrected reseal removed that packaging offender and rebuilt complete manifest/checksums without runtime, governed-test or workflow changes.
- **Technical C4 basis:** SHA-256 `09531e9b64dd66c558e3c2478ea897e020adfd4814a7237cd8eab7f18b568a86`; verification run `33509385291`, job `99861098139`, conclusion `success`; evidence artifact ID `9800985043`, digest `sha256:1a8074c08631910f28833a95cef45d8f85f0b9b0762740a65bfa050f5f80555f`.
- **Authoritative workflow:** `.github/workflows/api03-accept.yml`, exact sealed Git blob `2bc621dd168c5c9fa5bc0782ed2cecdde40a9e82`, SHA-256 `39a04b1a5d57c320f542889d81a5c6e9a2a30e6684d2bae49e4a82cbe5406e8d`; authoritative branch used the same blob for byte-for-byte binding.
- **Authoritative run:** `33511256210`, job `99867183151`, conclusion `success`, provenance commit `412a6fb3e5445a92d3792ceecd17649e4afd132d`.
- **Terminal result:** `API03_RESULT:PASS:validation/api03/authoritative_acceptance_result.json`; `22/22` acceptance gates completed successfully, no failed or environment-blocked gate.
- **Live/runtime evidence:** API-03 `99/99 PASS`, `0` failed, `0` skipped; PostgreSQL `16.15` / `server_version_num=160015`; workspace cryptography `46.0.7`; isolated cryptography `49.0.0` via offline wheelhouse; governed R11 V23 PASS; real multi-process mTLS/replay topology PASS; SEC-01 repository guard PASS.
- **Accepted predecessor:** API-02 C13 SHA-256 `9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9`, authoritative run `33497989489`, `ACCEPTED / CLOSED`.
- **Authoritative evidence artifact:** `api03-c5-authoritative-acceptance-33511256210`, artifact ID `9801733668`, size `9,563` bytes, digest `sha256:ccbf76b448ec634803330c0f5575a44bf50f50eae195cacfcfdfe53789987a78`, created `2026-09-01T13:05:41Z`, expires `2026-11-30T13:04:44Z`.
- **Acceptance decision:** `docs/api/API-03/API03_C5_ACCEPTANCE_RECORD.json`.
- **No-self-acceptance resolution:** `CANDIDATE_NOT_ACCEPTED` remains inside sealed C5 intentionally; independent authoritative acceptance plus the post-run governance record establishes canonical `ACCEPTED / CLOSED`.
- **Open blockers for API-03:** none.
- **Scope consequence:** API-03 is closed at exact corrected C5. API remains open through API-06. No production-readiness, legal-activation, final-security, BSI/CC or EAL4 certification claim follows.
- **Next permitted primary stage:** `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`.


### INFRA-02 authoritative transition — 2026-09-02

- **Previous state:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED` in the independently reviewed candidate line; no canonical INFRA-02 acceptance/closure had yet been recorded on `main`.
- **New state:** `INFRA-02 ACCEPTED / CLOSED`.
- **Governing candidate:** `EPD2_INFRA02_CI_CD_AND_SOFTWARE_SUPPLY_CHAIN_CANDIDATE_0.1.zip`.
- **Candidate SHA-256:** `d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c`.
- **Candidate size:** `15,980,332` bytes.
- **Accepted predecessor:** INFRA-01 C3 SHA-256 `5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131`.
- **Authoritative run:** `33574647511`, job `100075828121`, conclusion `success`.
- **Independent proof:** exact transport PASS; seal/freeze PASS; exact predecessor delta `35/11/0/1450`; targeted tests `146/146 PASS`; canonical harness `51/51 PASS`; current-run evidence `INFRA01_EVIDENCE_RESULT:PASS`; package member-content identity `1496/1496`; terminal `INFRA02_AUTHORITATIVE_RESULT:PASS`.
- **Authoritative evidence artifact:** `infra02-authoritative-evidence-33574647511`, ID `9826333069`, wrapper SHA-256 `4fada409e8fe58f861a0615e2606d5e26615e815b2da6126f430a583b045e5b1`.
- **Exact reviewed candidate artifact:** `infra02-authoritative-candidate-33574647511`, ID `9826333641`, wrapper SHA-256 `69bdcf1210f7ef371513f41d22d32bed42bf25ab81dd2aa5a244aca95ec17ab6`.
- **Post-run reconciliation:** freshness gate observed `main@b359c575b224727a9b69cabc1ea3f3bf63a2f64c`; before closure, `main` advanced to `4b95cc952897bd78fe912a2737f53e66264d6ff1`. Concurrent changes were the authoritative API-05 PCR closure and formatting-only API-05 governance helper. Classification `NO_INFRA02_CONTROLLING_CONFLICT`; API-05 closed/API-06 next state is preserved.
- **Acceptance decision:** `docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json`.
- **Open blockers for INFRA-02:** none.
- **Scope consequence:** bounded INFRA-02 closes at the exact candidate above; overall INFRA remains open and INFRA-03…INFRA-07 are not promoted. No production-readiness, legal-activation, BSI/CC/EAL4 or final-security claim follows.
- **Next permitted primary program stage:** unchanged — `API-06 = NEXT`.

---

## 7. Branch / reconciliation discipline

There is exactly one canonical Program Control Register. A branch reads the target/current register as entering state, changes only evidence-supported facts, never silently resets newer state, and never creates a competing control register. At merge, reconcile against the target branch's current copy.

---

## 8. Required repository gate

Governed cumulative candidates should fail when any canonical bootstrap/control/master file is absent, a competing register exists, the control register contradicts the candidate's governed stage, or the register is stale after a status transition.

---

## 9. Immediate execution decision

**Primary implementation:** `API = CLOSED` through exact independently accepted `API-06 C1`. The current governed checkpoint is `INFRA/OPS PREVIEW-READINESS MINIMUM`; OPS-03 qualification may now bind the exact accepted API-06 runtime.

**Governed forward path:** qualify the explicit INFRA/OPS preview-readiness minimum against the exact accepted API runtime and then, only by a separate checkpoint-opening decision, open `SYSTEM TRIAL PREVIEW — FIRST END-TO-END PROBNIK`. The preview is an early usable-system checkpoint only and cannot close INFRA or OPS. After preview findings are handled through owning-layer lineage, complete INFRA → OPS → CTRL → FRONT, establish `FINAL INTEGRATION`, and run final SEC against that exact integrated baseline before the final readiness decision.

**Integration scheduling:** existing INTEGRATION-01 lineage is preserved, but no automatic new INTEGRATION-01 candidate is required after each API stage. Full authoritative integration is normally deferred until FRONT is closed; earlier targeted integration work is permitted only when a concrete compatibility blocker or acceptance dependency requires it.

**Parallel OPS action:** bounded `OPS-01 — Operational Readiness, Incident, Recovery & Change Control Foundation` is `ACCEPTED / CLOSED` at exact C2 SHA-256 `39a6b02af03269a8ebf61216503fa03df2abf4e5194aa3c45c6f4bb176f2ad27`. This accepted foundation may be reused by later preview/final OPS work, but it does not close the overall OPS layer or authorize production operation. API is now closed; OPS-03 qualification must independently bind the exact accepted API-06 identity.

**Parallel INFRA action:** bounded `INFRA-02 — CI/CD & Software Supply-Chain Integrity` is `ACCEPTED / CLOSED` at exact SHA-256 `d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c`, authoritative run `33574647511`. Its accepted build-once, SBOM/provenance, vulnerability/history-secret, promotion-by-digest, drift-detection and release-integrity foundation may be reused by later INFRA work. This does not close the overall INFRA layer, open or accept INFRA-03…INFRA-07, or select a hosting provider. API is now closed; INFRA remains separately governed.

**Parallel FRONT action:** FRONT-02 specification is established. The next legitimate FRONT-02 step is completion/acceptance of the mandatory specification artefacts named in `FRONT-02-SPECIFICATION.md`, followed by implementation within that scope. API is now closed; this FRONT work still does not constitute FRONT acceptance or final closure and remains downstream of the governed preview/integration path.

**Parallel PILOT action:** PILOT-04 C9 is `ACCEPTED / FROZEN` and PILOT-05 C3 is `ACCEPTED / ESTABLISHED`; neither requires another acceptance rerun. PILOT-06 remains `NOT_STARTED_AS_GOVERNED_STAGE` until it is explicitly opened for governed pilot findings/corrections. Neither accepted PILOT stage claims production readiness/legal activation or forces immediate INTEGRATION-01 advancement; API closure does not alter their own governed acceptance lineage.

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
10. This decision changes no mobile-stage status. The current primary implementation position is `API-06 = NEXT`; API-04 is `ACCEPTED / CLOSED`; FRONT-MOBILE-02 is not started, FRONT is not closed, and no mobile/production/security readiness is claimed.
