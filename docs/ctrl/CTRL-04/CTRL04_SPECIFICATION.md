# CTRL-04 Specification — Governed Operations Console

**Mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED` · **Self-state:** `CANDIDATE_NOT_ACCEPTED`

## 1. Placement

CTRL-04 lives in the installed control-plane service
(`services/control-plane-service/src/epd2_control_plane_service/`) as three
modules and one HTML file:

| Module | Owns |
| --- | --- |
| `operations_console.py` | typed records, action catalogue, policy switches, the `OperationsConsoleService` lifecycle, commit-time reauthorization, evidence, checkpoint/restore, read models |
| `operations_adapters.py` | the `OperationsAdapter` contract, redaction/scrubbing, `ReferenceOperationsAdapter`, `LocalProcessAdapter` (real process restart), `LocalFilesystemBackupAdapter` (real archive backup/restore), `JsonFileStore` |
| `operations_api.py` + `operations_console.html` | HTTP JSON API over the service and the single-page console |

It reuses, unchanged, the CTRL-01 `EvidenceJournal` (`audit.py`), the CTRL-02
`AuthorityDirectory`/`AuthorityGrant`/`ExactScope`/`ApproverClass`
(`regional_operations.py`) and the CTRL-03 `Ctrl02State` adapter
(`credential_lifecycle.py`). No file installed by the CTRL-01/02/03 canonical
manifests is modified; gate G05 verifies the CTRL-03 installed payload byte-for-byte.

The console is registered under the CTRL-01 registry's `CONSOLE_OPERATIONS` /
`DESK_PLATFORM_OPERATIONS` desk; every action code is prefixed `OPS.`.

## 2. Data model

All records are frozen dataclasses with explicit identity and version fields.

| Record | Key fields |
| --- | --- |
| `OperationalTarget` | `target_id`, `target_class` (SERVICE, ENVIRONMENT, JOB_QUEUE, INTEGRATION, DATASTORE, BACKUP_SET), `domain` (GENERAL, VOTING), `environment` (PRODUCTION_LIKE, NON_PRODUCTION), `scope: ExactScope`, `deployment_identity_ref`, `adapter_id`, `version`, `capabilities` |
| `DeploymentIdentity` | `deployment_id`, `artifact_digest` (sha256), `artifact_ref`, `release_ref`, `change_ref`, `version`, `verified` |
| `HealthSnapshot` | `state` (HEALTHY, DEGRADED, UNAVAILABLE, UNKNOWN), `deployment_identity_ref`, redacted `details`, `redacted_fields` |
| `JobQueueSnapshot` | `queue_id`, `state`, `depth`, `oldest_age_seconds` |
| `OperationalActionRequest` | immutable `action_id`, `request_id`, `idempotency_key`, `action_type`, `impact`, `actor_ref`, `session_id`, `authority_ref`+`authority_version`, `target_id`+`target_version`, `deployment_identity_ref`, `environment`, `scope_key`, `parameters`, `parameters_digest`, `policy_version`, `ctrl02_revision`, `ctrl03_trust_revision`, `requested_at`, `expires_at`, `state`, `approval_state`, `execution_state`, `result_state`, `review_state`, `approval_ids`, `execution_id`, `result_id`, `incident_ref`, `maintenance_window_ref`, `backend_operation_ref` |
| `OperationalApproval` | `approval_id`, `approver_ref`, `approver_class`, `authority_ref`+`authority_version`, `session_id`, `approved_at`, `expires_at` (30 min), bound `parameters_digest`/`target_version`/`deployment_identity_ref`, `state` |
| `OperationalExecution` | `execution_id`, `executor_ref`, `executor_authority_ref`, `adapter_id`, `dispatched_at`, `deadline` (30 min), `state`, `backend_operation_ref` |
| `OperationalResult` | `result_id`, `state`, `failure_classification`, scrubbed `detail`, redacted `backend_metadata`, `redacted_fields` |
| `OperationalEvidenceRef` | `evidence_id`, `journal_sequence`, `event_hash`, `evidence_digest` |
| `BackupRestoreOperationRef` | `operation_id`, `kind`, `backup_set_id`, `backup_identity_digest`, `state`, `action_id` |
| `MaintenanceWindowRef` | `window_id`, `target_id`, `state` (REQUESTED, ACTIVE, EXPIRED, CLOSED), `starts_at`, `ends_at`, `action_id` |
| `OperationalIncidentRef` | `incident_id`, `target_id`, `severity`, `state`, `linked_action_ids` |
| `ConsoleSession` | `session_id`, `principal_id`, `state`, `expires_at`, `read_only` |
| `AuthorityProjection` | keyed-digest-signed, 5-minute projection of one CTRL-02 grant |

State enumerations: `ActionState` (REQUESTED, AWAITING_APPROVAL, APPROVED,
EXECUTING, SUCCEEDED, FAILED, PARTIAL_FAILURE, CANCELLED, EXPIRED, UNSUPPORTED,
REFUSED), `ApprovalState` (NOT_REQUIRED, PENDING, GRANTED, EXPIRED,
INVALIDATED), `ExecutionState` (NOT_DISPATCHED, DISPATCHED, RUNNING, COMPLETED,
FAILED, PARTIAL, TIMED_OUT, UNSUPPORTED), `ResultState` (PENDING, SUCCEEDED,
FAILED, PARTIAL_FAILURE, CANCELLED, EXPIRED, UNSUPPORTED), `ReviewState`,
`FailureClassification` (NONE, PROVIDER_FAILURE, PARTIAL_PROVIDER_FAILURE,
TIMEOUT, UNSUPPORTED_CAPABILITY, AUTHORIZATION_REFUSED, PRECONDITION_FAILED,
CANCELLED, EXPIRED, ADAPTER_UNAVAILABLE).

## 3. Action catalogue

| Action | Impact | Backend capability | Production approval | Non-production approval | Requester may execute |
| --- | --- | --- | --- | --- | --- |
| `OPS.STATUS.READ`, `OPS.HEALTH.READ`, `OPS.JOBS.READ`, `OPS.INTEGRATION.READ`, `OPS.DEPLOYMENT_IDENTITY.READ`, `OPS.RECOVERY_READINESS.READ`, `OPS.BACKUP.STATUS.READ`, `OPS.INCIDENT.READ`, `OPS.ACTION_HISTORY.READ`, `OPS.EVIDENCE.LOOKUP` | READ | — | — | — | (`OPS.READ`) |
| `OPS.SERVICE.RESTART` | MEDIUM | RESTART | INCIDENT_COMMANDER | none | yes |
| `OPS.DEPLOYMENT.ROLLBACK` | HIGH | ROLLBACK | INCIDENT_COMMANDER + SECURITY | INCIDENT_COMMANDER | no |
| `OPS.MAINTENANCE.ENTER` | MEDIUM | MAINTENANCE | INCIDENT_COMMANDER | none | yes |
| `OPS.MAINTENANCE.EXIT` | LOW | MAINTENANCE | none | none | yes |
| `OPS.JOB_QUEUE.PAUSE` | MEDIUM | QUEUE_CONTROL | INCIDENT_COMMANDER | none | yes |
| `OPS.JOB_QUEUE.RESUME` | LOW | QUEUE_CONTROL | none | none | yes |
| `OPS.BACKUP.REQUEST` | MEDIUM | BACKUP | INCIDENT_COMMANDER | none | yes |
| `OPS.RESTORE.REQUEST` | DESTRUCTIVE | RESTORE | INCIDENT_COMMANDER + SECURITY + TRUST_CUSTODIAN | INCIDENT_COMMANDER + TRUST_CUSTODIAN | no |
| `OPS.INCIDENT.LINK` | LOW | (console-owned) | none | none | yes |

Every mutating action carries commit-time reauthorization and immutable
evidence. Parameters are allow-listed per action, bounded, and identifier
parameters (`backup_set_id`, `window_id`, `incident_id`, `linked_action_id`)
must be single safe path segments; digests must be 64 hex characters.
`RESTORE` additionally requires `confirmation = CONFIRM-DESTRUCTIVE:<target_id>`.
Maintenance windows are bounded to 8 hours; requests expire after 4 hours.

## 4. Authorization decision input

At request, approval, commit and review the decision input is: actor and session
(server-side `ConsoleSession`, state and read-only flag), the signed authority
projection and the live CTRL-02 grant it must still match (grant id, version,
usability, approver class), action type, exact target identity and version,
environment, region/organization scope, parameters digest, `POLICY_VERSION`,
approval state and each approval's bound digest/target/deployment and approver
authority/session, current deployment identity, CTRL-02 revision/restrictions/
quarantines, and (rollback) the CTRL-03 trust-set revision and attestation.
Every decision is recorded as an `AuthorizationDecision` on the action and the
outcome is journaled, refusals included.

A principal holding any wildcard (`*`) or universal (`ADMIN`, `SUPER_ADMIN`,
`ROOT`) capability in the directory is refused every act (`OPS_UNIVERSAL_ADMIN_FORBIDDEN`).

## 5. Execution and results

`commit()` performs reauthorization, takes the per-target concurrency guard and
dispatches through the adapter. A `DispatchAck` moves the action to
`EXECUTING`/`DISPATCHED` with `result_state = PENDING`; only `resolve()`, which
polls the adapter's own report, produces a terminal result. Dispatch refusal,
adapter exception, unavailable adapter, missing capability and deadline
exhaustion are each terminal with their own classification. A timed-out target
stays guarded until a late backend outcome is observed and journaled as
`LATE_BACKEND_OUTCOME`; the timed-out result is never rewritten.

## 6. Evidence

Every transition appends to the CTRL-01 hash-chained `EvidenceJournal` with the
actor, authority basis, action type, scope, target, result, reason code,
approval references and the action id as correlation reference. Attributes are
redacted, secret-named keys are dropped and listed in
`evidence_redacted_fields`, free text is scrubbed, and the journal's own screen
refuses secret material. `evidence_record(action_id)` assembles the
`epd2.ctrl04.evidence.v1` record (schema in `CTRL04_EVIDENCE_SCHEMA.json`),
including refused requests that never became actions.

Persistence uses `JsonFileStore` (atomic rewrite). On load, every journal record
is re-appended and must reproduce its hash and sequence, the anchor must match,
the keyed `EvidenceSealer` seal must verify (a rewritten and re-chained history
cannot forge it without the key), and every action's state, result, failure
classification and actor must be backed by its journal trail.

## 7. API

Session header `X-EPD2-Session` names a server-side session; the browser holds no
authority. Client bodies carrying `state`, `approval_state`, `execution_state`,
`result_state`, `result`, `authority_ref`, `projection`, `signature`, `approvals`,
`outcome` and similar fields are refused (`OPS_BROWSER_STATE_NOT_AUTHORITATIVE`).
`/ops/v1/shell`, `/exec`, `/ssh`, `/sql`, `/secrets` answer
`OPS_DIRECT_EXECUTION_SURFACE_ABSENT`. Reads are filtered to targets in scopes
where the principal holds `OPS.READ`; every route checks session usability.
Internal errors are answered as `OPS_INTERNAL_REFUSAL` without a traceback.

Routes: `GET /ops/v1/{catalogue,me,targets,status,health,jobs,integrations,deployment-identity,recovery-readiness,backups,maintenance,incidents,actions,actions/{id},evidence/{id},read-model}`;
`POST /ops/v1/actions`, `/ops/v1/actions/{id}/{approve,commit,resolve,cancel,review}`.

## 8. UI

The single-page console distinguishes health (HEALTHY/DEGRADED/UNAVAILABLE),
action states, production-like vs non-production targets, exact artifact
digest/release/change references, action provenance and evidence references,
and prints why an action is unavailable (unsupported by backend, adapter
unavailable, missing right, read-only session). HIGH and DESTRUCTIVE requests
open a modal that requires the exact confirmation phrase; a mismatch is not
sent. All server values are HTML-escaped at ingestion. Controls are shown only
where the principal holds the right, and the server re-authorizes regardless.

## 9. Verification artefacts

`scripts/ctrl04_validator.py` (52 executable gates), `scripts/ctrl04_mutation_suite.py`
(48 source mutants, each must be DETECTED), `scripts/ctrl04_e2e_journeys.py`
(J01–J20 over real HTTP with real local adapters), `scripts/ctrl04_browser_journeys.py`
(B01–B04 with Chromium), `scripts/build_ctrl04_candidate.py` and
`scripts/verify_ctrl04_package.py`. Evidence lands in `validation/ctrl04/`.
