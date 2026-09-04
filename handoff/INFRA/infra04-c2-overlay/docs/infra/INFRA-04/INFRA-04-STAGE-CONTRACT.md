# INFRA-04 — Resilience, Recovery & INFRA Closure Readiness

**Stage state:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`
**Candidate state:** `CANDIDATE_NOT_ACCEPTED`
**Self-acceptance:** `false` — acceptance is external, and this stage does
not record one for itself.

**Candidate revision:** `C2` — freshness/reseal correction over live `main@7544f5dc3bf40304ae81b4d8ef476cc8ecb60ec5`. C2 changes no INFRA-04 runtime invariant: it preserves the accepted CTRL-05 canonical overlay, removes stale/nonexistent `__pycache__` entries from the changed-file lineage, recomputes every changed-file digest after final evidence generation, and requires a complete independent rerun before any acceptance.

INFRA-04 answers one question about the accepted preview runtime: *when
something breaks, does the system stay honest?* It adds no new capability
and no new trust root. It adds the ability to fail, recover, and prove
afterwards that nothing was quietly weakened along the way.

## 1. Bound predecessors

| Stage | Exact accepted identity | Record |
| --- | --- | --- |
| INFRA-01 C3 | `5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131` | `docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json` |
| INFRA-02 | `d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c` | `docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json` |
| INFRA-03 C1 | `6b49e02dbf38f9672c02c2540af051e3684cb4278b4330e91909e454f379d3c1` | `docs/infra/INFRA-03/INFRA03_C1_ACCEPTANCE_RECORD.json` |
| API-06 C1 | `3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c` | `docs/api/API-06/API06_C1_ACCEPTANCE_RECORD.json` |

The artifact the drills actually deploy is the accepted INFRA-02 candidate,
byte for byte. Its digest is recomputed from the file at gate time and
compared against the accepted identity above — a stage that claims a
predecessor it did not run is claiming nothing.

INFRA-04 consumes **no runtime dependency** from OPS-03. The canonical
register records OPS-03 C3 as **`ACCEPTED / CLOSED`**. INFRA-04 neither
consumes OPS-03 as a predecessor nor infers OPS-layer closure or any
INFRA-04 acceptance from that state. G08 classifies adjacent dependency
claims against the canonical acceptance records and fails stale or false
claims.

## 2. The ten invariants

| | Invariant | Where it is enforced |
| --- | --- | --- |
| I1 | Readiness has levels, and they are not interchangeable | `readiness.assess`, G12–G15 |
| I2 | A stale or missing consequential dependency forbids authority | `readiness.assess`, J03/J04 |
| I3 | Recovery may not weaken a control | `recovery.check_posture_preserved`, `config_ext.check_no_weakening`, G33/G40–G42 |
| I4 | A restore has an exact, re-proven identity | `backup.check_restore_preconditions`, J08–J11 |
| I5 | There is at most one durable writer per role | `continuity.prove_fence_exclusive`, G23 |
| I6 | The voting domain is untouched by INFRA machinery | `backup.BACKUP_ALLOWLIST`, J17, G44–G46 |
| I7 | Recovery is provider-neutral | `recovery.RecoveryOrchestrator`, no cloud primitive anywhere |
| I8 | Evidence carries secret *references*, never values | `evaluators.check_no_secret_values`, G39 |
| I9 | A recovery is a six-phase evidenced chain, and evidence is append-only | `recovery.RecoveryEvidence`, `LedgerChain`, G47/G48 |
| I10 | No self-acceptance, no certification, no production-readiness, no layer closure | `evaluators` claim scanners, G09/G54 |

## 3. Readiness levels

```text
PROCESS_ALIVE → SERVICE_REACHABLE → SERVICE_READY → DEPENDENCY_READY → AUTHORITATIVELY_READY
```

States: `STARTING`, `READY`, `DEGRADED_READ_ONLY`, `NOT_READY`,
`EXPLICITLY_UNAVAILABLE`.

The ladder is monotone and every downgrade carries a reason. Two properties
matter more than the ladder itself:

* **Authority is not reachable from a broken dependency.** A consequential
  dependency that is unavailable *or stale* caps the service at
  `SERVICE_READY / DEGRADED_READ_ONLY`. Read capacity survives; authority
  does not, and the limitation is named.
* **Authority requires the fence.** A declared durable writer that does not
  hold its advisory lock is `DEGRADED_READ_ONLY` whatever its dependencies
  say. Readiness, `/authz-ready` and the consequential path can therefore
  never disagree with each other.

## 4. Recovery contracts

Every recovery produces a chain with all six phases, in order:

```text
trigger → pre_state → action → result → post_verification → readiness
```

A chain missing a phase is `I04_RECOVERY_EVIDENCE_INCOMPLETE`. It is not a
recovery with a gap; it is an unexplained state change.

Contracts: **restart**, **restore**, **rejoin**, **rollback**, each with a
measured bound recorded in `infra/runtime/resilience_policy.json`. The
bounds are evidence bounds observed in a single-host preview runtime. They
are not availability promises, and a drill that exceeds its bound fails the
gate rather than being re-labelled.

## 5. Fencing

The durable-writer fence is a session-scoped PostgreSQL advisory lock in
namespace `0x45504432`, taken on the database the runtime already depends
on. No coordination service and no provider primitive is introduced (I7).

The fence session is fed its statement over a pipe the writer holds open.
This is deliberate: a `pg_sleep` session outlives its parent, and an
orphaned holder would keep both the lock and a connection after the writer
it represents is gone. With the pipe, the session ends when the writer dies
by any means, including `SIGKILL` — which is exactly the lifetime a fence
must have. G23 proves the full cycle live: claim, contend, crash, re-claim.

## 6. Drift

Four identity planes are baselined while the runtime is known good and
compared afterwards: **runtime bytes**, **configuration**, **schema and
migrations**, **trust material**. Drift is reported, never adopted. An
**unobservable** plane counts as drift, because a plane that cannot be read
cannot be shown to match — though a read is retried before that verdict, so
one timed-out probe under load is not mistaken for a changed byte.

## 7. Acceptance targets

| Target | Result |
| --- | --- |
| Gates | 54/54 PASS (53 runtime phase, G53 package phase) |
| Mutation classes | 48/48, each mapped to its own distinct `I04_*` detector |
| E2E / recovery drills | 18/18 PASS, live |

The verdict vocabulary is `PASS`, `FAIL`, `BLOCKED`,
`NOT_APPLICABLE_GOVERNED`. There is no "pass with environment limitation":
a gate that cannot execute is `BLOCKED`, and a blocked gate blocks the seal.

## 8. What this stage does not claim

It does not accept itself. It does not close the INFRA layer — the register
records `INFRA = OPEN / NOT CLOSED` and that decision is not the
candidate's to make. It asserts no production readiness, no legal
activation and no certification of any kind. The only marker it emits is
`INFRA04_PRESEAL_RESULT`, which means developer pre-seal and nothing more.
