# INFRA-01 — Known Limitations

**Stage:** `INFRA-01 — CI Acceptance Harness & Release-Integrity Foundation`
**Mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`

An environment limitation documented here does not satisfy canonical
acceptance. The canonical verdict remains fail-closed: a stage that cannot
execute is `FAIL`/`BLOCKED`, never `PASS WITH ENVIRONMENT LIMITATION`.

## L-01 — Foundation, not full closure, for the release/readiness FIRs

The deployment-manifest schema/validator (`FIR-REL-001`) and readiness
contract/evaluator (`FIR-READY-001`) are canonical mechanisms with fail-closed
semantics and adversarial unit coverage, but no live service is wired onto
them yet — INFRA-01 deploys nothing. Signing of release manifests, promotion
workflows, drift detection against running environments and launch-control
integration remain later INFRA/OPS work. Per Master Register §30, these FIRs
are not marked implemented merely because a reference interface exists.

## L-02 — Secret scanning covers content handed to it, not yet Git history

The HI-08 gate scans the tracked tree, staged/generated material, the final
archive bytes and persisted evidence. Full public Git-history/ref scanning —
required by `FIR-SEC-SECRET-001` for the public-release gate — is a designed
extension point (the scanner takes arbitrary content), not yet an executed
control. The detector set is deterministic and pattern-based; entropy-based
detection can be added without changing the gate's fail-closed contract.

## L-03 — Gateway non-ownership checks are structural, not semantic

HI-11 enforcement is mechanical: forbidden domain imports in infrastructure
Python code and domain-decision markers in workflow definitions. It cannot
prove the absence of domain semantics reimplemented under other names. The
full `FIR-API-001` checker set (gateway package dependency rules, action
mappings terminating in the owning service) belongs to the API-line gateway
codebase, which does not exist on this source lineage; the structural checks
here prevent the _infrastructure_ side from accreting domain logic.

## L-04 — Browser/visual evidence is environment-anchored

The Playwright/axe/visual suites run against the repository's pinned
runtime-resolution mechanism (`@sparticuz/chromium` extraction). Visual
snapshots are those approved in the repository; a materially different
render host could legitimately fail them. The canonical run records platform
and tool inventory in the manifest so an independent reviewer can judge
comparability. This is recorded transparency, not a waiver: a red visual
gate stays red.

## L-05 — This source lineage is the governed v1.1 Git baseline, not the PACK-26C1 ZIP lineage

The Entering Baseline Identity v1.1 fixes INFRA-01 to
`epd2-civic-os@8ff32c3e…` (repository version 0.16.0), which does not contain
the later PACK-17…PACK-26 candidate-line services or their local-CI driver.
Checks that exist only in that ZIP lineage (e.g. the PACK-17B suites, the
`epd2-verify` wheel-isolation stage) are therefore not in this registry; the
registry governs every check present on this baseline. Reconciling the two
lineages is a governance matter outside INFRA-01's authority and was not
attempted (no reconstructed tree, per the baseline rule).

## L-06 — Baseline defects fixed forward, disclosed

The entering baseline was red on `ruff check .` (2 errors),
`make typecheck` (10 errors) and `npm run format:check` (145 files under the
locked Prettier), its default pytest run mutated two frozen PACK-16D
artifacts (the PACK-25C6 defect class, absent on this lineage), and
`test_property_limitation_is_recorded` asserted that `hypothesis` is not
installable — false in any healthy frozen environment. All five are fixed
forward in this candidate with no check weakened (four normative/evidence
artifacts are byte-preserved via `.prettierignore` instead of reformatted);
details in the implementation report §3. The frozen-artifact pins in
`frozen_artifacts.json` pin the _entering-baseline_ bytes, which remain
byte-identical in this candidate.

## L-07 — GitHub workflow not yet exercised on GitHub

`.github/workflows/infra01-acceptance.yml` invokes exactly the same command
proven locally, but an authoritative GitHub Actions execution of this
workflow on the exact candidate commit has not been performed in this round
(the candidate is delivered from the local canonical run). Running it is
part of the independent governed acceptance path, not of developer handoff.
