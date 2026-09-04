# INFRA-04 Developer Report

**Stage:** Resilience, Recovery & INFRA Closure Readiness
**Self-state:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`
**Candidate state:** `CANDIDATE_NOT_ACCEPTED`
**self_acceptance:** `false`

Acceptance is external. This report is a developer pre-seal statement and
records no acceptance, no production readiness, no certification and no
INFRA-layer closure.

**C2 correction status.** C1 established the runtime design and prior developer measurements, but its exact-byte changed-file manifest was stale and its canonical target was superseded by the independently accepted CTRL-05 C1 transition. C2 is therefore a mandatory rebase/reseal, not an acceptance carry-over. All gate/mutation/drill results below are targets and prior C1 observations until the C2 GitHub runner reproduces them on the exact C2 bytes.

## 1. Result

| Target | Required | Achieved |
| --- | --- | --- |
| Governed gates | 54/54 PASS | 53/53 runtime phase, G53 in the package phase |
| Mutation classes | 48/48 detected | 48 classes, 48 distinct `I04_*` detectors |
| E2E / recovery drills | 18/18 PASS | 18/18 PASS, live |

The verdict vocabulary is `PASS`, `FAIL`, `BLOCKED`,
`NOT_APPLICABLE_GOVERNED`. A gate that cannot execute is `BLOCKED` and
blocks the seal; there is no "pass with environment limitation" anywhere in
this stage.

## 2. Canonical base and predecessors

* Canonical target for C2: `main@2018b2d07f380c16e75da9dcfc889de4cdafdfc2`
  tree `31767f4cf4f9fe213e03652d4bdc35c638aca916`
  commit timestamp `2026-09-03T23:48:23+00:00`
* Master maintenance level: `V26`
* INFRA layer state read from the register: `OPEN / NOT CLOSED`

Accepted predecessors are bound by digest and by the governance record that
accepted them. The artifact the drills deploy is the accepted INFRA-02
candidate, byte for byte, recomputed at gate time.

## 3. Measured recovery bounds

These are bounds observed in a single-host preview runtime on this run.
They are evidence, not availability promises.

| Recovery | Measured | Governed bound | |
| --- | --- | --- | --- |
| `dependency_recovery_to_authoritative` | 2.909s | 60s | within bound |
| `database_restart_to_ready` | 1.139s | 90s | within bound |
| `service_restart_to_ready` | 2.254s | 45s | within bound |
| `restore_to_ready` | 0.884s | 180s | within bound |
| `rollback_to_verified` | 3.557s | 120s | within bound |

## 4. Gate results

| Gate | Title | Result |
| --- | --- | --- |
| `G01` | fresh canonical main commit/tree recorded | `PASS` |
| `G02` | PCR current state reconciled | `PASS` |
| `G03` | Master/FIR current state reconciled | `PASS` |
| `G04` | exact INFRA-01 accepted identity bound | `PASS` |
| `G05` | exact INFRA-02 accepted identity bound | `PASS` |
| `G06` | exact INFRA-03 accepted identity bound | `PASS` |
| `G07` | exact API-06 accepted identity/reconciliation bound | `PASS` |
| `G08` | unaccepted OPS/CTRL dependencies not falsely claimed accepted | `PASS` |
| `G09` | candidate self-state remains CANDIDATE_NOT_ACCEPTED | `PASS` |
| `G10` | environment inventory deterministic | `PASS` |
| `G11` | environment isolation preserved | `PASS` |
| `G12` | process-alive distinct from service-ready | `PASS` |
| `G13` | service-ready distinct from authoritative-ready | `PASS` |
| `G14` | stale consequential dependency => NOT_READY / fail closed | `PASS` |
| `G15` | unavailable consequential dependency => explicit unavailable | `PASS` |
| `G16` | no silent weaker fallback mode | `PASS` |
| `G17` | controlled restart proof | `PASS` |
| `G18` | controlled service recovery proof | `PASS` |
| `G19` | dependency outage proof | `PASS` |
| `G20` | network-unreachable dependency proof | `PASS` |
| `G21` | database outage behaviour | `PASS` |
| `G22` | database recovery/reconnect behaviour | `PASS` |
| `G23` | ambiguous writer / split-brain refused or safely fenced | `PASS` |
| `G24` | backup creation identity deterministic | `PASS` |
| `G25` | backup integrity verification | `PASS` |
| `G26` | restore point identity exact | `PASS` |
| `G27` | wrong-environment restore refused | `PASS` |
| `G28` | incompatible schema/migration restore refused | `PASS` |
| `G29` | corrupted backup refused | `PASS` |
| `G30` | restore post-consistency verification | `PASS` |
| `G31` | restore post-readiness verification | `PASS` |
| `G32` | rollback is bounded and verified | `PASS` |
| `G33` | rollback does not weaken auth/security controls | `PASS` |
| `G34` | restart/recovery loop bounded | `PASS` |
| `G35` | drift detection catches runtime byte drift | `PASS` |
| `G36` | drift detection catches configuration drift | `PASS` |
| `G37` | drift detection catches schema/migration drift | `PASS` |
| `G38` | trust/certificate/JWKS drift handled according to policy | `PASS` |
| `G39` | secret material absent from evidence/logs/package | `PASS` |
| `G40` | mTLS/service identity preserved across recovery | `PASS` |
| `G41` | authorization/session revocation semantics preserved | `PASS` |
| `G42` | commit-time reauthorization semantics unaffected | `PASS` |
| `G43` | idempotency/replay semantics unaffected | `PASS` |
| `G44` | voting isolation preserved | `PASS` |
| `G45` | no persistent member/person identifier introduced into voting domain | `PASS` |
| `G46` | no general INFRA route gains voting-domain reach | `PASS` |
| `G47` | recovery evidence chain complete | `PASS` |
| `G48` | post-recovery audit/evidence continuity | `PASS` |
| `G49` | System Trial infrastructure replay executed unchanged | `PASS` |
| `G50` | environment-blocked trial cases owned by INFRA re-evaluated | `PASS` |
| `G51` | full inherited INFRA regression | `PASS` |
| `G52` | mutation suite target | `PASS` |
| `G54` | independent authoritative review required; self_acceptance=false | `PASS` |
| `G53` | package exact-byte seal verified pre/post authoritative execution | executed by the package phase |

## 5. Drill results

| Drill | Title | Result |
| --- | --- | --- |
| `J01` | clean deployment from the exact accepted baseline | `PASS` |
| `J02` | readiness transitions STARTING -> READY only after dependencies | `PASS` |
| `J03` | dependency loss transitions READY -> NOT_READY/degraded correctly | `PASS` |
| `J04` | dependency recovery returns to READY only after verification | `PASS` |
| `J05` | PostgreSQL outage produces fail-closed consequential behaviour | `PASS` |
| `J06` | PostgreSQL recovery restores service without duplicate effect | `PASS` |
| `J07` | controlled service restart preserves security/session semantics | `PASS` |
| `J08` | backup created with deterministic identity and verified digest | `PASS` |
| `J09` | corrupted backup restore is refused | `PASS` |
| `J10` | wrong-environment restore is refused | `PASS` |
| `J11` | valid restore completes and passes consistency/readiness checks | `PASS` |
| `J12` | rollback to the exact governed target completes and is verified | `PASS` |
| `J13` | unauthorised runtime/config drift is detected | `PASS` |
| `J14` | trust/certificate/JWKS inconsistency fails safely | `PASS` |
| `J15` | evidence continuity survives restart/recovery | `PASS` |
| `J16` | idempotent retry after restart returns the same governed result | `PASS` |
| `J17` | voting-isolation/privacy boundary remains intact | `PASS` |
| `J18` | unchanged System Trial infrastructure replay reports a real result | `PASS` |

## 6. System Trial replay

The governed harness is replayed unchanged: the five input documents hash
to their bound digests, and none is written by this stage.

| Scenario | Name | Owner | Result |
| --- | --- | --- | --- |
| `F-01` | service unavailable | OPS | `PASS` |
| `F-02` | database unavailable | OPS | `PASS` |
| `F-03` | session revoked mid-journey | API | `ENVIRONMENT_BLOCKED` |
| `F-04` | authority revoked mid-workflow | CTRL | `ENVIRONMENT_BLOCKED` |
| `F-05` | time or expiry anomaly | CTRL | `ENVIRONMENT_BLOCKED` |
| `F-06` | partial dependency outage | OPS | `PASS` |
| `F-07` | operator recovery | OPS | `PASS` |
| `F-08` | rollback and reset | OPS | `PASS` |
| `F-09` | stale browser state | CTRL | `ENVIRONMENT_BLOCKED` |
| `F-10` | voting-linkable identifier observed in a log | CTRL | `PASS` |
| `F-11` | real personal data observed in the preview | OPS | `PASS` |
| `F-12` | cross-scope data leak observed | API | `ENVIRONMENT_BLOCKED` |

Overall: `INFRA_OWNED_SCENARIOS_PASS_REMAINING_BLOCKERS_OUTSIDE_INFRA04`. The trial GO/NO-GO decision is
`NOT_DECIDED_BY_INFRA04` — it is not INFRA-04's to make. Of the
capability-matrix entries blocked by an INFRA dependency,
21
of 22 now have their INFRA
precondition met; the rest name the layer that still blocks them.

## 7. Governance reconciliation

No region of the Program Control Register contradicts another about a stage
this candidate consumes. Several regions do **lag**: they do not yet
restate an acceptance that a recorded governance decision already proves.
That is reported rather than resolved, and acceptance is taken only where a
record exists.

| Stage | Acceptance carried by | Not yet carried by |
| --- | --- | --- |
| `CTRL-01` | layer_table, primary_position | immediate |
| `CTRL-04` | layer_table, primary_position | immediate |
| `INFRA-01` | layer_table, primary_position | immediate |
| `INFRA-03` | primary_position | immediate, layer_table |
| `OPS-01` | immediate, layer_table | primary_position |
| `OPS-02` | layer_table | immediate, primary_position |

OPS-03 is recorded as `QUALIFICATION_ELIGIBLE`, not accepted. INFRA-04
consumes nothing from it.

## 8. What was found in the inherited baseline

Canonical main does not pass its own canonical acceptance harness: ruff
lint, ruff format, `make typecheck` and Prettier all fail on the pristine
tree, and the acceptance harness itself was never installed. Both were
repaired in separate, clearly-scoped commits ahead of the stage work, with
every change behaviour-neutral. The full list, including the observations
handed back to the API, FRONT and governance lines, is in
`INFRA-04-KNOWN-LIMITATIONS.md`.

## 9. Marker

The only permitted marker is:

```text
INFRA04_PRESEAL_RESULT:PASS:<sha256>:<size>
```

It means developer pre-seal. It is never an `AUTHORITATIVE_RESULT`, and an
independent authoritative review is required before this candidate may be
accepted.
