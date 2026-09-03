# CTRL-04 — Developer Report

**Stage:** `CTRL-04 — Operations Console`
**Mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`
**Self-state:** `CANDIDATE_NOT_ACCEPTED`
**Date:** 2026-09-03

This report claims no CTRL-04 acceptance, no CTRL-layer closure, no production
readiness, no legal activation, no final security acceptance and no BSI or
Common Criteria certification. The developer emits only a PRESEAL marker.

## 1. Bootstrap

Fresh clone of canonical `main`:

| Field | Value |
| --- | --- |
| repository | `nepogoda1970-epd2/epd2-civic-os` |
| commit | `8a4d336589f2322984dbf03b1af3b5a575643005` |
| tree | `ee38a1a51f70f4c9652dd75eab4d0d1034d7135c` |

Read in order: `EPD2_PROJECT_ENTRYPOINT.md`, `EPD2_PROGRAM_CONTROL_REGISTER.md`
(state: `CTRL-01/02/03 ACCEPTED / CLOSED; CTRL LAYER OPEN`, `OPS-03 QUALIFICATION
ELIGIBLE`, INFRA-03…07 not promoted), the relevant Master Register sections
(`FIR-CTRL-001`, `FIR-GOV-004`, `FIR-GOV-005`, `FIR-SEC-004`, `FIR-TRUST-002`,
`FIR-OPS-001`, `FIR-OSS-007`, `FIR-VOTE-NET-001`), the CTRL-01 specification and
registry, the CTRL-02/03 acceptance records and stage contract, the installed
CTRL-03 runtime, and the INFRA-01/02 and OPS-01/02 acceptance records plus the
OPS-02 preview-readiness disposition. The starter ZIP was treated as the
assignment, not as a baseline; its manifest template was reused.

The pre-existing control-plane suite reproduced at `290 passed` before any
CTRL-04 file was added.

## 2. What was built

| Item | Count / fact |
| --- | --- |
| governed actions | 19 (10 read, 9 mutating; 1 HIGH, 1 DESTRUCTIVE) |
| typed records | 14 frozen dataclasses (all twelve required plus `ConsoleSession`, `AuthorityProjection`) |
| rights | `OPS.READ / REQUEST / APPROVE(class) / EXECUTE / REVIEW`, resolved from the CTRL-02 exact-scope directory |
| policy obligations | 28 explicit switches, all enforced; `OperationsPolicy.governed()` only |
| refusal reason codes | 56 |
| adapters | reference (injectable), real local process supervisor, real filesystem backup/restore |
| HTTP routes | 17 read (incl. UI and catalogue), 6 mutation; 5 explicitly absent surfaces |
| CTRL-04 tests | 94 (cumulative suite 384 passed, 0 failed, 0 skipped) |
| gates | 52/52 PASS, every gate an executed probe |
| mutation fixtures | 48/48 DETECTED |
| E2E journeys | J01–J20, 20/20 PASS over real HTTP |
| browser journeys | B01–B04, 4/4 PASS in Chromium (screenshots in `validation/ctrl04/browser/`) |

Detail is in `CTRL04_SPECIFICATION.md`; the contract is `contracts/control/ctrl04_operations_console.json`.

## 3. Design decisions worth flagging

**The accepted OPS/INFRA runtimes are not on `main`.** Canonical `main` carries
their acceptance records, not their payloads. CTRL-04 therefore binds to
OPS-01/02 and INFRA-01/02 by exact accepted identity (gates G06/G07, verified
against the records on `main`) and speaks only its own adapter contract.
The E2E journeys run the governed control semantics over that contract with
real local mechanisms: `LocalProcessAdapter` really terminates and re-spawns an
operating-system process and derives health from the live replacement;
`LocalFilesystemBackupAdapter` really writes content-addressed archives and
restores them; `JsonFileStore` really persists evidence that a re-instantiated
console re-verifies. The evidence file classes this as
`REFERENCE_AND_LOCAL_REAL_ADAPTERS` and states that it is not a
provider-integration claim. Mock-only success was not used, but neither is
provider integration claimed.

**Authority is CTRL-02's, not CTRL-04's.** Grants, versions, approver classes and
exact scopes come from `regional_operations.AuthorityDirectory`. CTRL-04 adds a
signed, five-minute `AuthorityProjection` and always re-resolves the live grant;
a principal holding any wildcard capability is refused everything. CTRL-02
restrictions and quarantines arrive through the CTRL-03 `Ctrl02State` adapter
and are checked for requester, approver and executor sessions with revision
pinning between request and commit. CTRL-03 is bound through an explicit
trust-set adapter for rollback attestation and the TRUST_CUSTODIAN approval
class for restore.

**Dispatch is a pending state.** `commit()` returns `EXECUTING` with
`result_state = PENDING`; only `resolve()` reading the adapter's own report
produces a terminal result. Dispatch refusal, adapter exception, missing
capability and deadline exhaustion each have their own terminal classification.
A timed-out target stays guarded until a late outcome is observed.

**Evidence is the truth, tables are projections.** Persisted checkpoints are
re-verified record by record, sealed with a key that never enters the file, and
every action's state, result, classification and actor must be backed by its
journal trail on load.

## 4. Independent adversarial review, and what it found

The first candidate was put through an adversarial review whose brief was to
find places where the implementation is weaker than it appears. It found real
defects. They are recorded here, with their resolution, because a reviewer
should know that a first pass produced them. Each fix carries a test in
`tests/test_ctrl04_hardening.py` that reproduces the defect.

| Finding | Why it mattered | Resolution |
| --- | --- | --- |
| The HTTP layer checked only that a session *existed*; revoked or expired sessions could still list targets/actions, read the read model and drive `resolve`. | Hard requirement 9 held for mutations only. | Every route now checks session usability; refused with the session's reason code. |
| Checkpoint action/result tables were restored verbatim, and a rewrite that recomputed the whole hash chain and in-file anchor loaded cleanly. | "No historical evidence mutation" held only against naive edits. | Keyed `EvidenceSealer` over the anchor; tables cross-checked against the journal on load (state, result, classification, actor); re-chained and table-forged checkpoints are refused and gate G13 proves both. |
| Adapter `detail` strings were not redacted; keys ending in `_id`/`_version` (e.g. `secret_id`, `token_id`) were exempt from redaction; a secret marker in `purpose` made the whole read model raise for every principal. | Secret material could reach UI/API/evidence, and one requester could deny the read model to everyone. | Free-text scrubbing on details, purpose and read model; reference exemption narrowed to `_ref`/`_reference(_id)`; the read model scrubs instead of failing. |
| CTRL-02 quarantine/restriction was checked only for the requester's session and never at approval. | Hard requirement 4 was partial. | Checked at approval for the approver, at commit for the executor, and every approver's session is re-checked at commit. |
| `backup_set_id` was any string, so a backup archive could be written outside the backup root. | Path traversal through a governed identifier. | Identifier parameters must be single safe segments; digests must be 64 hex characters; the adapter refuses paths outside its root. |
| An exception from `adapter.dispatch` left the action `APPROVED` with a dangling execution and no evidence; a second commit dispatched again. | Duplicate execution with lost evidence. | Dispatch exceptions terminate as `FAILED / ADAPTER_UNAVAILABLE` with evidence; an action carrying an execution id can never be committed again. |
| Malformed input (`duration_minutes="abc"`, an idempotency key with whitespace, a non-string `incident_ref`, a bad route shape) crashed instead of refusing. | "Every refusal is evidence-bearing" was violated. | Converted to `OPS_PARAMETER_INVALID` refusals with journal records; the API answers `OPS_INTERNAL_REFUSAL` without a traceback for anything unexpected. |
| Read-only sessions could review and cancel. | Hard requirement 11. | Refused; review decisions are now recorded like the others. |
| `/ops/v1/read-model` leaked windows/backups/incidents outside the reader's scope. | Scope filtering was incomplete. | All collections filtered. |
| Evidence for a refused request could not be looked up over HTTP even though the id was journaled. | Immutable action ids were partly unreachable. | The evidence route answers refused ids, scoped by the recorded scope key. |
| The UI built rows with unescaped `innerHTML`. | A registrar-supplied identifier could execute script under the page's CSP. | All server values are HTML-escaped at ingestion. |
| Mutation and E2E results were not bound to the runtime bytes; G12 matched a mutant's exact text. | Stale evidence could pass; a gate measured a string, not a property. | Result files carry a runtime source digest that G50/G51 compare; G12 now probes prefix-, parent- and wildcard-scope grants behaviourally. |

Findings the review classified as incidental detection, kept and disclosed:
M06 (changed parameters digest) and M47 (unsigned projection) are defence in
depth — the tampered parameters and the forged projection are both caught by a
second, independent check, so each mutant is detected only by the reason code
of the other check. M16 is detected by the typing difference `UNSUPPORTED`
versus `FAILED`, which is the property. M12 binds CTRL-03 as an artifact trust
set and a required approval class, not as an organizational-authority source,
because CTRL-03 owns credential/trust lifecycle rather than organizational
authority.

## 5. Observed conditions in the canonical baseline

Recorded, not resolved.

**`PCR-CTRL04-STATE-ABSENT`.** The Program Control Register names CTRL-01/02/03
and says the CTRL layer is open, but records no CTRL-04 execution state (no
`ACTIVE / IN DEVELOPMENT` line). The starter package supplies that state. Per
the entrypoint's update rule, the governed acceptance of this candidate should
record the CTRL-04 transition.

**Repository-wide `mypy scripts` fails on `main` before CTRL-04** (30 errors in 8
pre-existing files, e.g. `scripts/api06/…`). CTRL-04's own scripts and runtime
type-check clean with the service source on the path; the whole-repository
`make typecheck` target is not a green gate on the baseline and is not claimed
here.

**Pre-existing failing test** noted in the CTRL-01 report
(`voting-service/tests/reference/test_property.py`) is unchanged and outside
this stage's suite.

## 6. Known limitations

- The projection signer and its verifier run in one process in the reference
  deployment, so the signed-projection mechanism is exercised but its
  separation value only materialises when the authority source is remote.
- Sessions are server-side records identified by an opaque header; the
  reference deployment has no session issuer, origin binding or step-up. This
  is a boundary, not a claim.
- Redaction is marker- and pattern-based. A secret stored under an innocuous
  key with an unrecognisable value is not caught; the journal additionally
  refuses known secret shapes.
- `LocalProcessAdapter` performs the restart synchronously inside `dispatch`;
  the console still treats the acknowledgement as pending until `resolve()`.
- Checkpointing rewrites the whole state on every mutation; adequate for the
  reference world, not a production persistence design.
- The console restart in J19 re-instantiates the service from the persisted
  file in the same process; the managed local processes keep running.
- The CTRL-01 `EvidenceJournal` markers are narrower than CTRL-04's redaction
  set; CTRL-04 compensates before appending. The installed CTRL-01/02/03 files
  were deliberately left byte-identical (gate G05).

## 7. Before any future seal

1. Re-fetch current `main` and re-run G01; a drifted baseline is a
   reconciliation obligation.
2. Reconcile OPS-03 and INFRA-03 if either is accepted by then; bind their
   exact identities or keep them recorded as not accepted.
3. Re-run mutation, E2E and browser journeys after any runtime change; G50/G51
   refuse evidence whose runtime digest does not match.
4. Re-record the freeze deliberately, then verify against it, then seal, then
   post-verify the sealed bytes.
