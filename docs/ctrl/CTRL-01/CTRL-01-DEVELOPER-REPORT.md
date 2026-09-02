# CTRL-01 — Developer Report

> **CTRL-01 C1 canonical reconciliation — 2026-09-02.** This candidate is
> reconciled to canonical `main@217559b7f21c338d6fe8d4e4676082cd3840251c`. P1 statements that API-05,
> INFRA-02 or OPS-02 were not accepted are historical and superseded for current-state
> interpretation. Their exact accepted governance records are bound by Git blob identity.
> API-06 remains `NEXT / NOT ACCEPTED`; the API layer remains open and System Trial
> Preview remains `CHECKPOINT_NOT_OPEN`. This bounded CTRL-01 acceptance does not claim
> `overall CTRL-layer closure`, production readiness, legal activation, or BSI/Common Criteria certification.


**Stage:** `CTRL-01 — Governed Control Plane & Authority Operations Foundation`
**Stage mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`
**Date:** 2026-09-02
**Self-state:** `CTRL01_IMPLEMENTATION_COMPLETE / LOCAL_VERIFICATION_PASS / PRESEAL_READY / NOT_ACCEPTED`

This report claims no CTRL acceptance, no CTRL closure, no production readiness,
no final security acceptance, no BSI or Common Criteria certification and no
legal activation. It opens no System Trial Preview checkpoint.

## 1. Bootstrap

The canonical baseline was taken from the repository, not from the starter
package. `main` was cloned fresh and resolved to:

| Field | Value |
| --- | --- |
| repository | `nepogoda1970-epd2/epd2-civic-os` |
| branch | `main` |
| commit | `217559b7f21c338d6fe8d4e4676082cd3840251c` |
| tree | `eb8a3254c2b8a30feff71318d4377eff2435605c` |

That commit is identical to the baseline the starter package recorded, so there
was no drift to reconcile at development start. All four canonical documents and
all six acceptance-record files named in the package manifest were verified by
git blob SHA against the manifest and matched exactly; the two records the
manifest listed without a SHA (`FRONT-03-C1`, `FRONT-02-C2.1`) plus `INFRA-01 C3`
and `OPS-01 C2` were located and read.

Read in order before implementation: `EPD2_PROJECT_ENTRYPOINT.md`,
`EPD2_PROGRAM_CONTROL_REGISTER.md`, the relevant sections of
`EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` (`FIR-CTRL-001`, `FIR-GOV-004`,
`FIR-GOV-005`, `FIR-SEC-004`, `FIR-TRUST-002`, `FIR-TRUST-003`),
`EPD2_BSI_VOTING_BOOTSTRAP_RULE.md`, and the four governance models in
`docs/governance/`.

## 2. What was built

A working control-plane service, an executable twenty-two-gate validator, a
thirty-seven-mutation anti-cheat corpus, and the System Trial Preview
preparation harness. Counts, all measured rather than asserted:

| Item | Count |
| --- | --- |
| governed actions in the inventory | 48 (43 mutating, 5 read-only) |
| consoles / desks | 6 / 27, plus 3 explicit `NO_UI` decisions |
| control API contracts | 48, covering all 11 required console capabilities |
| separation-of-duties rules | 9 |
| negative authorization scenarios | 20 required, 23 implemented |
| commit-time reauthorization cases | 8, plus a baseline control case |
| governed checks | 28 |
| mutations, all detected by their expected check | 37 |
| packaged tests | 178 |
| mandatory gates | 22, all PASS |

Full detail is in `docs/ctrl/CTRL-01/CTRL-01-SPECIFICATION.md`. Evidence is in
`validation/ctrl01/`; the trial harness is in `validation/system_trial_preview/`.

## 3. Design decisions worth flagging

**Scope containment is exact-match, not hierarchical.** `Scope.contains` answers
"is this the same scope", never "is this at or above that scope". A Bund office
reaches a Land only through an oversight grant that equals the single scope its
source decision names — so both widening the grant and re-pointing it at a
different Land fail closed. This is the mechanical form of `FIR-GOV-005`
section 1.

**Platform scope is not the top of the hierarchy.** `ScopeLevel.PLATFORM`
exists for technical operations and carries no party-organ competence; a gate
proves no platform authority holds a governance action code.

**CTRL-01 imports no code from the accepted API stages.** Those runtimes live in
sealed candidate archives, not in this working tree. CTRL-01 binds to their
accepted governance semantics by reference and states so explicitly in
`dependency_reconciliation.json`. A later integration must re-derive those
bindings against the exact accepted bytes.

**The runtime route table is maintained separately from the inventory.**
`routes.py` is a second source, not a projection, because reconciling an
artifact against itself proves nothing.

**Enforcement obligations are explicit switches.** `ControlPolicy` has one
boolean per obligation, all enforced, and the mutation suite flips them one at a
time. A candidate whose checks still pass with an enforcement removed has proved
nothing, and this is how that is demonstrated rather than asserted.

## 4. Independent review, and what it found

The work was put through an adversarial review whose brief was to find places
where the implementation is *weaker than it appears* — checks that pass for the
wrong reason, mutations detected by something unrelated, and gates whose findings
list can never be non-empty. It found real defects. They are recorded here rather
than quietly fixed, because the fact that a first pass produced them is
information a reviewer of this stage should have.

| Defect | Why it mattered | Resolution |
| --- | --- | --- |
| The Bund-takeover check probed a principal holding no oversight grant, so it was refused by ordinary scope isolation. Deleting the oversight enforcement left the whole suite green. | Hard constraint 2 defeated with a passing suite. | The check now probes the fixture's actual oversight holder, in two vectors (widened, re-pointed), with a baseline assertion that the legitimate single-scope grant still resolves. Oversight is bound to the scope its source decision names. |
| The mass-assignment check restated an inventory constant. `ControlRequest.parameters` was written and read by nothing, so a real injection path was caught by nothing. | W11's "hidden privileged field mass-assigned" was unmodelled. | Parameters are now constrained to a governed allow-list and an unknown key is refused; the check drives a real injection attempt and asks whether the acting authority widened; `MUT-18` models a runtime that merges caller fields onto the authority. |
| The evidence chain had no external anchor, so deleting the newest record, or rewriting a record and recomputing every hash forward, both validated cleanly. | Hard constraint 8. The corpus modelled only the two easy tampering shapes. | `append` maintains a (count, head) anchor outside the record list; `verify` and `recompute_chain` compare against it. `MUT-16B` and `MUT-16C` were added for the two hard shapes. |
| The universal-admin check required all twelve rights and every action id — shapes a real root account never has. | Hard constraint 1. An authority with 11 of 12 rights and every mutating action code passed. | Three shapes are now rejected: all rights, every operative right (all but review), and every mutating action code. `MUT-01` was rewritten to the realistic shape. |
| G22 verified a manifest against the same files it had just hashed in the same process. | The same-bytes rule was unenforced; a file edited after verification passed. | The recorded baseline is read from disk *before* this run computes anything, and `--record-freeze` is required to re-record. Verified by editing a packaged file and observing G22 fail. |
| G13 and G16 had structurally unreachable findings; G18 restated a constant. | Three gates measured nothing. | G13 drives every mutating contract with an unauthorized principal and requires a refusal; G16 inspects the policy the runtime actually holds and probes unknown-action and unknown-session behaviour; G18 probes the privacy screen and measures its budget. |
| The break-glass renewal check scanned attribute names. | A renewal path named anything else would pass. | Replaced with a behavioural probe over every public method that takes a grant id. |
| Four SoD responsibilities were never assigned by the runtime, so three rules could not fire. | G07 evidence overstated what was proved. | `SECRET_VISIBILITY`, `CREDENTIAL_ISSUANCE`, `EMERGENCY_GRANT` and `EMERGENCY_REVIEW` are now assigned in `_check_sod`. |
| `check_no_direct_state_mutation` compared two different populations and tolerated one un-evidenced write. | A single silent authority change passed. | Every directory write must now carry a governed writer; one un-attributable write fails the check. |
| Two negative scenarios were the same assertion, and one did not isolate the right from the action code. | W8 counted them as distinct coverage. | The Bund check now tests a different mechanism; `test_12` gives the auditor the action code but not the right. |
| `_tamper_remove` / `_tamper_rewrite` shipped in the production evidence module. | The frozen candidate carried a working history-rewrite primitive. | Moved into `mutations.py`, the attacker model. G17 now fails if the evidence module ships any `_tamper*` helper. |

Each fix was verified by re-applying the exploit and confirming the suite fails.

## 5. Observed conditions in the canonical baseline

Recorded, not resolved. `EPD2_PROJECT_ENTRYPOINT.md` section 3 forbids silently
choosing the older statement, so these go to governed reconciliation.

**`PCR-API04-STATE`.** The Program Control Register's section 2 phase-state table
says `API-04 ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`, while the same section's
"current primary position" block, section 3 and section 9 all say
`API-04 = ACCEPTED / CLOSED` with `API-05` active.
`docs/api/API-04/API04_C1_ACCEPTANCE_RECORD.json` records
`decision: ACCEPTED_CLOSED` dated 2026-09-02, corroborating the latter. CTRL-01
consumes no API-04 contract in a way that depends on which statement is current.

**`PCR-API04-TRANSITION-MISSING`.** Section 6 requires every status transition to
record previous/new state and governing evidence. Subsections exist for FRONT-02
C2.1, PILOT-04 C9, PILOT-05 C3, API-01, API-02 C13 and API-03 C5 — but not for
API-04, whose acceptance record nevertheless exists.

**Pre-existing failing test, unrelated to CTRL-01.**
`services/voting-service/tests/reference/test_property.py::test_property_limitation_is_recorded`
asserts that `hypothesis` cannot be imported, but `hypothesis>=6.112,<7` is in
the repository's own `dev` dependency group, so `make setup` makes this test
fail. It fails identically with CTRL-01 removed. Reported, not touched.

## 6. Dependencies not relied upon

`API-05`, `INFRA-02` and `OPS-02` are **ACCEPTED / CLOSED as bounded stages**; `API-06` remains **NEXT / NOT ACCEPTED** and are recorded
as open dependencies in `validation/ctrl01/dependency_reconciliation.json`.
Operator-reported working status was not substituted for a governance record. No
working ZIP, local PASS, branch name or self-authored claim was treated as
acceptance. API-01's acceptance exists as a Program Control Register transition
with no acceptance-record file on `main`; that is recorded explicitly rather than
being read as unaccepted.

## 7. Before any future seal

1. Re-fetch current `main` and re-run G01; a drifted baseline is a reconciliation
   obligation.
2. Reconcile the exact accepted identity of API-05 and API-06, or record each
   explicitly as not yet accepted.
3. Reconcile INFRA-02 and OPS-02 if either is accepted by then.
4. Re-read both canonical registers.
5. Re-run every affected gate after any predecessor delta.
6. Re-record the freeze baseline deliberately, then verify against it.

## 8. Known limitations

- The control plane is a governed model with an in-memory reference world. It has
  no persistence layer, no HTTP transport and no wiring into the accepted API
  runtimes; the API contracts are declarations, exercised through the reference
  runtime rather than over a network.
- Approver *session* state is not re-checked at commit. Approver authority,
  authority identity, credential state and active restrictions are. An approver
  does not act at commit time, so this boundary is deliberate — but it is a
  boundary, not full coverage.
- The System Trial Preview harness is preparation only. No environment exists, so
  no journey is `SUPPORTED_REAL_PATH` today; 24 of 26 are `BLOCKED_BY_DEPENDENCY`
  and one is `UNSUPPORTED_FOR_TRIAL` pending separate lawful authorization. The
  target column records what each journey should become once the checkpoint
  opens, and is a plan, not evidence.
- The trial journey catalogue is hand-authored. Its declared runtime paths are
  not cross-checked against a deployed system, because there is none.
- `FIR-CTRL-001` is not closed by this stage. CTRL-01 supplies the registry,
  the action model and the tests; whole-FIR completion needs the integrated
  baseline.
