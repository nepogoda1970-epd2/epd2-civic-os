# CTRL-04 Stage Contract — Operations Console

## Status

`CANDIDATE_NOT_ACCEPTED`. Stage mode `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. The
candidate may emit only `CTRL04_PRESEAL_RESULT:PASS:<sha256>:<size>`; it never
emits `CANON PASS`, `ACCEPTED`, `CLOSED`, `CTRL LAYER CLOSED`, `PRODUCTION READY`
or any certification claim. Acceptance is an independent governed decision on
the exact sealed bytes.

## Scope

CTRL-04 is the governed operations control plane over operational capabilities
that INFRA/OPS/runtime domains already own. It exposes bounded, typed, auditable
read and action surfaces for deployment/runtime status, service and environment
health, jobs and queues, integration status, controlled restart, controlled
rollback where supported, bounded maintenance windows, backup and restore
requests and status, recovery readiness, incident linkage, deployment and
artifact identity, change/release references, action history and evidence.

CTRL-04 does **not** own or implement a container/orchestrator, a CI/CD engine,
a monitoring or logging backend, a backup or restore engine, secret storage,
PKI or key custody, voting infrastructure internals, political or governance
decision authority, raw database administration, or any shell/SSH surface.
Provider-specific execution stays behind the `OperationsAdapter` contract in
`operations_adapters.py`.

## Canonical dependency chain

`Operator → CTRL-04 authority check → bounded OPS/INFRA action → result → immutable audit/evidence`

## Mandatory lifecycle

`REQUEST → POLICY/AUTHORITY CHECK → OPTIONAL APPROVAL → COMMIT-TIME REAUTHORIZATION → EXECUTION DISPATCH → RESULT → EVIDENCE → REVIEW STATE`

Request, approval, execution, secret visibility and review are separate rights
(`OPS.READ`, `OPS.REQUEST`, `OPS.APPROVE` with an approver class,
`OPS.EXECUTE`, `OPS.REVIEW`) resolved from the CTRL-02 exact-scope authority
directory. No right implies another; no role label grants the set.

## Control invariants

- Exact region and organization scope; a "higher" scope grants nothing.
- A principal holding any wildcard/universal capability is refused every act.
- Approval, execution and review are distinct principals; the requester may
  not approve; an approver may not execute; a participant may not review.
- Commit-time reauthorization re-evaluates actor session, requesting authority
  version and usability, approver authority and session, target version,
  deployment identity, environment, scope, parameters digest, policy version,
  CTRL-02 revision/restrictions/quarantine and CTRL-03 artifact trust.
- Stale approval, stale authority, revoked/expired session, changed scope,
  changed target, changed deployment identity or changed parameters fail closed.
- Idempotency keys are mandatory; replays deduplicate, conflicts refuse,
  duplicate and conflicting executions are refused; adapters flag replayed
  execution ids.
- A dispatch acknowledgement is never success. Every action ends in exactly one
  of `SUCCEEDED`, `FAILED`, `PARTIAL_FAILURE`, `CANCELLED`, `EXPIRED`,
  `UNSUPPORTED` (or `REFUSED` before it exists), each with a failure
  classification.
- Unsupported backend capability is an explicit `UNSUPPORTED` state, never a
  simulated success.
- HIGH impact requires two approver classes; DESTRUCTIVE requires three, an
  exact confirmation phrase, a matching completed backup identity and an active
  maintenance window; neither may be executed by the requester.
- Rollback targets only an artifact attested by the CTRL-03 trust set and
  recorded as a verified deployment identity.
- Voting-domain targets are invisible and unreachable from the general console.
- Raw secrets never appear in UI, API, logs or evidence: metadata is redacted
  key- and value-wise, free text is scrubbed, secret-named keys are dropped from
  evidence, and the journal refuses secret material outright.
- Evidence is append-only, hash-chained, keyed-sealed on persistence, and the
  action tables must agree with the journal on every restart.
- The browser never supplies authority, approval state, execution state or
  results; such fields are refused, not ignored.

## Predecessor identities

| Stage | Decision | Candidate SHA-256 | Size |
| --- | --- | --- | --- |
| CTRL-01 C1 | `ACCEPTED / CLOSED` | `07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5` | 190099 |
| CTRL-02 | `ACCEPTED / CLOSED` | `f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e` | 16720456 |
| CTRL-03 C1 | `ACCEPTED / CLOSED` | `89fca0f6c975a7c0e1eb70c2e3ad5229830e781c91d86637a81f99e39ac7b0ff` | 16788860 |
| INFRA-01 C3 | `ACCEPTED / CLOSED` | `5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131` | 15854311 |
| INFRA-02 | `ACCEPTED / CLOSED` | `d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c` | 15980332 |
| OPS-01 C2 | `ACCEPTED / CLOSED` | `39a6b02af03269a8ebf61216503fa03df2abf4e5194aa3c45c6f4bb176f2ad27` | 16457357 |
| OPS-02 C3 | `ACCEPTED / CLOSED` | `ac3b543b0cb3a8e45f7d973c841769d0b4c6e7af649a54aee034f3e0b6afc125` | 16632939 |

INFRA-03 (`WORKING_PRESEAL_NOT_ACCEPTED`) and OPS-03 (`QUALIFICATION ELIGIBLE`,
not accepted) are recorded as non-authoritative and are not claimed as
dependencies. The accepted INFRA/OPS runtime payloads are not installed on
canonical `main`; CTRL-04 binds to them by exact accepted identity and adapter
contract only and imports none of their code.

## Acceptance boundary

Developer validation reports PASS only when all 52 gates pass, all 48 mutation
fixtures are detected, all 20 E2E journeys and all 4 browser journeys pass, the
freeze verifies on the same bytes, and package verification passes before and
after sealing. None of that is acceptance.
