# EPD² — BSI-CC-PP-0121 Certification-Readiness Matrix

**Status:** governed pre-evaluation readiness control — **NOT a BSI/CC conformance claim**  
**Introduced:** 2026-08-30  
**Target profile:** `BSI-CC-PP-0121`, _Protection Profile for E-Voting Systems for non-political Elections_, Version 1.0, CC:2022 Revision 1  
**Target assurance package:** `EAL4 + ALC_FLR.2`  
**Applies to:** all future implementation and material changes that affect EPD² Voting or the security-critical environment on which a certifiable voting TOE would depend.

## 1. Governance effect

This document is a certification-readiness control. It does **not**:

- certify EPD² Voting;
- assert `BSI compliant`, `CC compliant`, `EAL4`, `PASS`, `ACCEPTED`, `CLOSED`, production readiness or legal activation;
- reopen an already accepted historical stage merely because a later certification target was introduced;
- authorize statutory/public political elections under a PP whose stated product scope is non-political elections.

From the effective date forward, a Voting-affecting change must preserve a traceable path:

```text
BSI PP requirement / SAR
→ EPD² requirement
→ architecture / trust boundary
→ implementation
→ test
→ evidence
→ disposition
```

A known certification blocker may remain open only when it is explicitly recorded as a deferred gap with a responsible owner, rationale and required closure stage. A deferred gap is never evidence of certification, acceptance or closure.

## 2. Status vocabulary

- `GREEN — STRONG ALIGNMENT`: strong current design/reference evidence; formal evaluator acceptance still absent.
- `YELLOW — PARTIAL`: material evidence exists but production/evaluation evidence is incomplete.
- `RED — MATERIAL GAP`: production behavior/evidence is absent, deferred or explicitly blocked.
- `ORANGE — TOE/ST DECISION`: exact TOE/Security Target/evaluator interpretation must be fixed before certification-oriented architecture is frozen.
- `BLUE — EXTERNAL EVALUATION`: cannot be closed by EPD² self-assertion.

## 3. Current matrix

| ID   | Area                                                                     | Current readiness | Required closure                                                                                                                                            |
| ---- | ------------------------------------------------------------------------ | ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M-01 | TOE definition / strict PP conformance                                   | **ORANGE**        | Freeze exact certifiable TOE and draft Security Target. Decide single-server vs multi-component TOE.                                                        |
| M-02 | Voter identification / authentication / voters' register / voting record | **RED / P0**      | Obtain written evaluator position on EPD² non-identifying, election-scoped eligibility representation. Do not weaken identity↔ballot separation by default. |
| M-03 | Security roles / election-board separation                               | **YELLOW**        | Exact role mapping plus production authorization enforcement for critical operations.                                                                       |
| M-04 | Access control                                                           | **YELLOW**        | Production phase-aware RBAC/ABAC over all TOE interfaces and stores.                                                                                        |
| M-05 | Election-data import/export                                              | **YELLOW**        | Governed signed/approved election package, validation, authorization and export evidence.                                                                   |
| M-06 | Trusted channels to endpoints                                            | **RED**           | Production TLS/peer-auth profile, downgrade protection, current BSI cryptographic mapping and tests.                                                        |
| M-07 | Multi-component trusted channels                                         | **RED**           | If TOE is distributed, apply PP multi-component package and protect every inter-component exchange.                                                         |
| M-08 | Encrypted voting flow                                                    | **GREEN**         | Production voting-client integration and evaluator mapping remain.                                                                                          |
| M-09 | End-to-end verification                                                  | **GREEN**         | Freeze final verification semantics/evidence and evaluate final product.                                                                                    |
| M-10 | Voter feedback / verification data                                       | **YELLOW**        | Production receipt/feedback lifecycle without turning receipt into proof of vote choice.                                                                    |
| M-11 | Ballot secrecy / anti-assignment                                         | **GREEN**         | Preserve PACK-15/16 unlinkability and prove it in production infrastructure.                                                                                |
| M-12 | One effective vote / no revoting                                         | **GREEN**         | Production durability/concurrency proof around exactly-once eligibility use.                                                                                |
| M-13 | No early readout / controlled tally                                      | **GREEN**         | Preserve stricter EPD² no-intermediate-tally invariant through production cryptography and state machine.                                                   |
| M-14 | Election evaluation / rule sets                                          | **YELLOW**        | Remove current reference limitations and define certifiable election-rule profiles.                                                                         |
| M-15 | Stored ballot integrity                                                  | **GREEN**         | Production datastore and archive evidence.                                                                                                                  |
| M-16 | Audit generation / reliable time                                         | **YELLOW**        | Reconcile BSI audit timestamps/reliable time with EPD² anti-correlation logging so identity↔ballot linkage is not recreated.                                |
| M-17 | Audit protection / attack detection / review                             | **RED**           | Protected storage, authorized review, storage-full behavior, attack indicators, retention and external anchoring.                                           |
| M-18 | Archiving / signed export                                                | **YELLOW**        | Canonical signed archive, independent re-verification and proof that secrets are excluded.                                                                  |
| M-19 | Self-tests / secure states / recovery                                    | **RED**           | Implement TOE startup/phase/resume self-tests, recoverable and unrecoverable secure states, governed recovery.                                              |
| M-20 | Security-function management                                             | **RED**           | Production management plane for phase transitions and security-critical actions with election-board/quorum authorization.                                   |
| M-21 | Cryptographic algorithms / BSI guidance                                  | **YELLOW**        | Map every production primitive/protocol/provider to current BSI guidance and ST assignments.                                                                |
| M-22 | RNG / key destruction                                                    | **RED**           | Production entropy design, health/reseed policy, custody lifecycle and defensible zeroization/destruction.                                                  |
| M-23 | Side-channel-resistant secret operations                                 | **RED**           | Remove Python secret big-int operations from certifiable path; use vetted constant-time/native/HSM-backed implementation.                                   |
| M-24 | Development evidence (`ADV`)                                             | **YELLOW**        | Convert strong PACK evidence into formal security architecture, functional specification, implementation representation and modular design.                 |
| M-25 | Lifecycle / configuration management (`ALC`)                             | **YELLOW**        | Certification-grade CM, controlled build/release, development security, delivery and lifecycle evidence.                                                    |
| M-26 | Flaw remediation (`ALC_FLR.2`)                                           | **RED**           | Governed vulnerability intake, triage, correction, disclosure/advisory and update process with evidence.                                                    |
| M-27 | Preparative / operational guidance (`AGD`)                               | **YELLOW**        | Evaluator-ready installation, preparation and operational guidance, including self-test/security parameters.                                                |
| M-28 | Developer testing / coverage (`ATE`)                                     | **YELLOW**        | Formal SFR↔test coverage and final TOE test evidence.                                                                                                       |
| M-29 | Independent testing / vulnerability analysis                             | **BLUE**          | Recognised CC evaluation facility performs independent testing and `AVA_VAN.3` work; close findings.                                                        |
| M-30 | Operational environment / BSI TR-03169                                   | **RED**           | Hardened deployment, network segmentation, reliable time, monitoring, admin controls, availability, incident and recovery evidence.                         |
| M-31 | Product/legal scope                                                      | **ORANGE**        | Define in-scope certification product/use case. PP-0121 certification must not be marketed as general approval for statutory political elections.           |

## 4. Mandatory P0 decisions

### P0.1 — identity model compatibility

EPD² preserves a hard trust boundary:

```text
identity / membership
→ eligibility decision
→ minimal single-use continuation capability
→ voting domain
→ encrypted ballot
```

The voting domain must not receive civil identity, member identity, account identity, a persistent member identifier or a reverse-resolvable identifier, and identity-side and ballot-side records must not become pairable through ordinary application/infrastructure metadata.

Before changing that invariant for certification purposes, obtain a written pre-evaluation position from a recognised Common Criteria evaluation facility on this question:

> Can the mandatory BSI-CC-PP-0121 User Identity, voters' register and voting-record concepts be represented by a non-identifying, election-scoped, single-use eligibility representation that cannot be correlated to the ballot or to civil/member identity while preserving strict conformance?

A negative answer triggers a TOE/certification-strategy decision. It does **not** automatically authorize weakening the privacy invariant.

### P0.2 — TOE boundary

Choose and document one evaluation target before certification-oriented production architecture is frozen:

1. central voting-server TOE with identity/eligibility and surrounding Civic OS components outside the TOE; or
2. multi-component voting TOE with the PP multi-component trusted-channel package.

## 5. Mandatory certification-readiness gate for future work

For every Voting-related PACK/API/INFRA/OPS/CTRL/FRONT/SEC change, the handover/acceptance evidence must state:

1. which rows in this matrix are touched;
2. whether each touched row is improved, unchanged, deferred or regressed;
3. the exact evidence path;
4. any new blocker;
5. owner and required closure stage for every deferred blocker.

A Voting-related change must **not** receive a certification-readiness clearance when it creates an unrecorded blocker or silently weakens a stronger EPD² privacy/security invariant.

Certification-readiness clearance is separate from normal implementation acceptance and does not imply BSI/CC conformance.

## 6. Required future evaluator/evidence set

The certification workstream should produce, at minimum:

1. `EPD2_BSI_TOE_BOUNDARY.md`
2. `EPD2_BSI_SECURITY_TARGET_DRAFT.md`
3. `EPD2_BSI_PP0121_SFR_TRACEABILITY_MATRIX.md`
4. `EPD2_BSI_TSFI_CATALOG.md`
5. `EPD2_BSI_ADV_ARCHITECTURE.md`
6. `EPD2_BSI_ADV_FUNCTIONAL_SPECIFICATION.md`
7. `EPD2_BSI_ADV_MODULAR_DESIGN.md`
8. `EPD2_BSI_AGD_PREPARATIVE_PROCEDURES.md`
9. `EPD2_BSI_AGD_OPERATIONAL_GUIDANCE.md`
10. `EPD2_BSI_CONFIGURATION_MANAGEMENT_PLAN.md`
11. `EPD2_BSI_SECURE_DELIVERY_PLAN.md`
12. `EPD2_BSI_DEVELOPMENT_SECURITY_PLAN.md`
13. `EPD2_BSI_FLAW_REMEDIATION_PROCESS.md`
14. `EPD2_BSI_SFR_TEST_COVERAGE.md`
15. `EPD2_BSI_VULNERABILITY_ANALYSIS_INPUT.md`
16. `EPD2_BSI_TR03169_DEPLOYMENT_PROFILE.md`

Existing PACK-15/16 evidence is source material for these artifacts, not a substitute for formal Common Criteria evidence.

## 7. Certification sequence

```text
P0 identity-model / TOE feasibility pre-assessment
→ freeze candidate TOE
→ draft Security Target and exact PP assignments
→ productionize voting core and security-critical infrastructure
→ close secret-handling / trusted-channel / audit / recovery gaps
→ assemble EAL4 + ALC_FLR.2 evidence
→ internal PP/SAR pre-evaluation
→ recognised evaluation facility
→ independent testing + vulnerability analysis + remediation
→ BSI certification decision for a fixed product/version/configuration
```

## 8. Current claim boundary

Current EPD² Voting may be described as having **strong alignment in several verifiable-voting properties and an explicit BSI certification-readiness workstream**.

It must not currently be described as `BSI-certified`, `BSI compliant`, `CC compliant`, or `EAL4`.
