# INFRA-01 — C1 Correction Report

**Stage:** `INFRA-01 — CI Acceptance Harness & Release-Integrity Foundation`
**Correction:** `C1` — governance-freshness / acceptance-harness correction
**Business scope:** NONE
**Self-state:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED / CANDIDATE_NOT_ACCEPTED`

```text
INFRA-01 C1 CORRECTION CANDIDATE
LOCAL CANONICAL HARNESS: see INFRA-01-ACCEPTANCE-MATRIX.md
EXTERNAL GOVERNED ACCEPTANCE: NOT YET PERFORMED
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

## 1. Lineage

| field                             | value                                                                                                                                                                             |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| exact entering (C0) candidate     | `EPD2_INFRA01_CI_ACCEPTANCE_HARNESS_CANDIDATE_0.1.zip`                                                                                                                            |
| entering SHA-256                  | `3bb42509a9db56d34db2bade38a3e73af1a202599392e257c91f3b3627743210` (15,806,881 bytes, 1449 members)                                                                               |
| independent verdict on C0         | `REJECTED / CORRECTION REQUIRED` (findings INFRA01-C1-01, INFRA01-C1-02)                                                                                                          |
| target/current governance at seal | `nepogoda1970-epd2/epd2-civic-os` `main` commit `556821e0e5d550a4db601bbe92e4f4673a1bc3ff`, tree `95fb9c911db229cf589330531b14f41b7049235e`                                       |
| target PCR identity used          | Git blob `2269540db0d6955f5ec0999d0448b3af4ec196f1`, SHA-256 `8f27b4687d8fc1ea84084d1ee95824eda9cd58edcd504407592923d64a34d240`                                                   |
| target Master identity used       | Git blob `7f5c6a9a88f8e653b43dc542a595ac37bf7a0692`, SHA-256 `3cb40d8c46baa4126702a60cb3138b3776548eda4549fc4ec0dd6163c83c1a3d` (unchanged on target vs the v1.1 source baseline) |
| source lineage                    | unchanged: Entering Baseline Identity v1.1 (`8ff32c3e…`, repository 0.16.0, canon 0.8.0) — intentionally preserved per C1 §8; no API-02/API-03 runtime imported                   |
| C1 candidate archive              | `EPD2_INFRA01_CI_ACCEPTANCE_HARNESS_CANDIDATE_0.1_C1.zip`; exact SHA-256 in the delivery sidecar and the sealed execution manifest of the evidence bundle                         |

## 2. Finding dispositions

**INFRA01-C1-01 (stale current execution state) — CORRECTED.** The
candidate register is reconciled with the current target `main` register as
base plus the INFRA-01 branch additions (INFRA row, INFRA-01 transition
entry, locked-Prettier normalization). Current interpretation now reads
`API-01 = ACCEPTED / CLOSED`, `API-02 = ACCEPTED / CLOSED`,
`API-03 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`,
`INFRA-01 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. The exact API-02 C13
authoritative identity is preserved verbatim (candidate SHA
`9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9`, run
`33497989489`, evidence artifact ZIP SHA `ac5f940b98b58d18d1c7cde42314079bb1890bea3596cd5cad3997eeb1818f57`),
and `docs/api/API-02/API02_C13_ACCEPTANCE_RECORD.json` is carried into the
candidate. Historical statements remain as history.

**INFRA01-C1-02 (harness blind to stale governance) — CORRECTED.** New
mandatory registry check `governance.freshness-reconciliation` (registry
1.1.0) validates the sealed reconciliation record
`docs/infra/INFRA-01/INFRA01_GOVERNANCE_RECONCILIATION.json`: record
integrity, target-authority identification, exact candidate-register byte
binding, and region-anchored expected current-state facts
(`canonical files exist != unique != current`). The authoritative path
additionally compares the recorded target authority against the
reviewer-fetched current `main` register
(`uv run python -m scripts.acceptance verify-reconciliation --target-pcr …`,
a mandatory step in `.github/workflows/infra01-acceptance.yml`).

Reviewer's exact reproduction re-run on the corrected candidate: stale-mutating
the current API-02 state now yields `finding_count = 2`
(`GOVERNANCE_RECONCILIATION_MISMATCH`, `GOVERNANCE_TRANSITION_MISSING`) —
previously `finding_count = 0`.

## 3. New freshness detector codes

`RECONCILIATION_RECORD_MISSING`, `RECONCILIATION_INTEGRITY_FAILURE`,
`GOVERNANCE_RECONCILIATION_MISMATCH`, `STALE_GOVERNANCE_STATE`,
`GOVERNANCE_TRANSITION_MISSING`, `GOVERNANCE_REGION_MISSING`,
`TARGET_AUTHORITY_MISMATCH`.

## 4. Mutation results

| class                                                                | fixture             | result                                                                                                                            |
| -------------------------------------------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| M17 stale PCR current-state regression (rehashed into the record)    | `test_m17_…`        | detected — `STALE_GOVERNANCE_STATE`                                                                                               |
| M18 target-authority identity mismatch (record edited, not resealed) | `test_m18_…`        | detected — `RECONCILIATION_INTEGRITY_FAILURE`; authoritative-side variant `test_m18b_…` — `TARGET_AUTHORITY_MISMATCH`             |
| M19 branch silently lacks newer target transition                    | `test_m19_…`        | detected — `GOVERNANCE_TRANSITION_MISSING`                                                                                        |
| M20 preserved historical text with correct current state             | `test_m20_…`        | PASS (positive fixture — history is not rejected)                                                                                 |
| register edited after reconciliation (binding drift)                 | `test_pcr_edited_…` | detected — `GOVERNANCE_RECONCILIATION_MISMATCH`                                                                                   |
| M01–M16                                                              | unchanged           | all preserved and passing; 19 negative classes ↦ 19 distinct detector codes (`test_every_c1_mutation_class_has_its_own_detector`) |

The independent `47 passed` regression floor for the two harness test files
is preserved and extended (55 passing after C1); no existing test was
removed or diluted, and no control from C1 assignment §7 was weakened.

## 5. Exact C0→C1 change accounting

Machine-readable, exclusion-free path delta:
`docs/infra/INFRA-01/INFRA01_C0_TO_C1_EXACT_INVENTORY.json`. BSI V26 files
are byte-identical to their §9-pinned identities; frozen PACK-16D artifact
pins unchanged; `uv.lock`/`package-lock.json` unchanged.

> **Erratum (C2, INFRA01-C2-01).** The claim above was false for the
> delivered C1 archive: the C0→C1 inventory excluded the two packaging
> files `SHA256SUMS.txt` and `ACCEPTANCE/FREEZE-INVENTORY.json` and
> declared `modified = 12` where the exact archive-byte delta is
> `modified = 14`. The inventory is superseded by
> `INFRA01_C0_TO_C2_EXACT_INVENTORY.json`, which is measured from archive
> bytes with no exclusions and preserves this error record; the C1 sealed
> reconciliation record also carried a temporally impossible
> `reconciled_at` (INFRA01-C2-02) and is superseded by the resealed
> `/2`-schema record. This paragraph is retained unedited above as the
> historical statement; see `INFRA-01-C2-CORRECTION-REPORT.md`.

## 6. Developer verification

The complete canonical harness (43 governed checks including the new
freshness gate) was executed on the exact C1 candidate before handoff; the
full stage/result matrix is in `INFRA-01-ACCEPTANCE-MATRIX.md` and the
sealed `EXECUTION-MANIFEST.json` of the evidence bundle. Developer-local
PASS is not authoritative acceptance; the independent reviewer performs the
governed acceptance path per C1 assignment §13.
