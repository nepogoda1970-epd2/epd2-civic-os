# ADR-039: Record classification, retention, controlled destruction and Legal Hold

## Status

`accepted`

## Date

2026-07-26

## Context

A party organization is simultaneously obliged to delete records it no
longer has a basis to keep, and forbidden to delete records that are
subject to litigation, an audit, or a regulatory proceeding. Those two
obligations point in opposite directions, and the failure mode of every
naive implementation is the same: retention expiry is treated as a licence
to delete, a scheduled job runs, and material that a Legal Hold covered
disappears.

Two further failure modes are just as common and just as damaging:

- **Policy rewrite as a deletion channel.** If disposal eligibility is
  computed live from "the current retention policy", then editing the
  policy — shortening a ten-year schedule to zero days — instantly makes
  every governed record of that class deletable, with no separate
  decision, no authorization and no trace of what the schedule used to
  say.
- **Deletion without proof.** If destruction removes the record and
  nothing else, the organization afterwards cannot demonstrate _that_ the
  destruction was lawful, authorized, or even that it happened at all —
  which is precisely what it will be asked to demonstrate.

## Problem

How should a governed record move from "created" to "destroyed", such
that:

- retention expiry authorizes _evaluation_, never deletion;
- an active Legal Hold always wins;
- an _unknown_ hold state is not silently treated as "no hold";
- rewriting a retention policy cannot, by itself, authorize destruction of
  already-governed records;
- a destruction leaves durable proof; and
- a retried destruction command cannot mint a second, divergent proof?

## Considered options

- **Option A — retention field on each record, cron deletes when due.**
  Simplest. Legal Hold implemented as a boolean flag checked by the job.
- **Option B — two-step: eligibility evaluation, then delete.** Hold
  checked during evaluation.
- **Option C — three-step controlled workflow:** evaluate eligibility →
  issue a separate `DestructionAuthorization` bound to specific versions →
  execute, producing create-once `DestructionEvidence`. Hold re-checked at
  every step, with an explicit `indeterminate` hold state that fails
  closed.

## Decision

**Option C.** Concretely:

### 1. Classification and retention are versioned and explicit

`GovernedRecord` carries `record_class` and a `RecordSensitivity`
(`public`/`internal`/`confidential`/`restricted`), plus
`(retention_policy_id, retention_policy_version)`. `RetentionPolicy` is
append-only by `(policy_id, policy_version)`: superseding creates a NEW
version and sets `supersedes_policy_version`; a stored version is never
rewritten. `InMemoryRetentionPolicyStore.create_version` refuses a
same-version write with different content
(`RETENTION_POLICY_VERSION_CONFLICT`). This is what makes "which schedule
was this disposal decided under" permanently answerable.

### 2. Retention never starts implicitly

A `RetentionStartEvent` must exist before a due time can be computed. Its
absence is not "started at creation" — it is
`RETENTION_START_UNDETERMINED`, a fail-closed refusal. `RetentionTrigger`
is a closed enum (`created_at`, `case_closed_at`, `membership_ended_at`,
`contract_ended_at`, `processing_ended_at`), and the start event records
which trigger fired, when it occurred, and when that fact was recorded.

### 3. Destruction is a three-step workflow, never a delete

- `evaluate_disposal_eligibility` returns a `DisposalEligibility` value
  whose refusal order is fixed and observable: unresolved scope → unknown
  record → unknown policy version → _indeterminate hold_ → unknown
  retention start → active hold → not yet due. Each ineligible verdict
  carries the reason code that produced it.
- `authorize_destruction` re-runs that evaluation itself rather than
  trusting a caller-supplied verdict, and issues a
  `DestructionAuthorization` bound to the exact `retention_policy_version`
  _and_ `record_version` it was issued against.
- `execute_destruction` re-checks Legal Hold _again_, verifies the
  authorization is not stale, and creates `DestructionEvidence` exactly
  once.

The record's metadata row survives with `state=destroyed` and its
`destruction_evidence_id` attached. There is no delete method anywhere in
`storage.py` — not on `GovernedRecordStore`, not on any adapter — so
there is no ordinary CRUD path for a caller to reach for. That absence is
asserted by `tests/repository/test_service_boundaries.py` and by the
service's own `test_storage.py`.

### 4. Legal Hold has three states, not two

`LegalHoldStatus` is `active` / `released` / **`indeterminate`**. The
third is the load-bearing one: it is what a hold carries when its
authority source could not be confirmed, and every record it covers then
fails closed with `LEGAL_HOLD_STATE_UNKNOWN` rather than being treated as
unheld. `evaluate_hold_applicability` deliberately reports blocking and
indeterminate holds _separately_, because "we could not determine the hold
state" and "this record is not yet eligible" are different facts and
collapsing them would let an unknown state read as an ordinary not-due
answer.

Hold scope is additive across `record_ids`, `record_classes` and
`case_ids`, and is only ever matched inside the hold's own organization:
`LegalHold.covers` returns `False` for a foreign record even when the
record id matches exactly.

Release is explicit, timestamped, appended to the hold's own append-only
`history`, and never implicit — a hold does not expire. Releasing an
already-released hold is `LEGAL_HOLD_TRANSITION_INVALID`.

### 5. Only destructive dispositions are hold-blocked

`DESTRUCTIVE_DISPOSITION_ACTIONS` is `{delete, anonymize}`. `archive` and
`review` are non-destructive and stay available while a hold is in force,
so a held record can still be moved into managed storage or put in front
of a reviewer. Blocking those too would make holds operationally
unworkable without protecting anything.

### 6. A policy supersession invalidates standing authorizations

`supersede_retention_policy` rebinds every affected non-destroyed record
to the new version via `GovernedRecord.rebound_to_policy_version`, which
resets `state` to `active` and drops `destruction_authorization_id`. A
fresh evaluation and a fresh authorization are then required. If a caller
tries to execute against the old authorization anyway, the version binding
catches it (`DESTRUCTION_AUTHORIZATION_STALE`), and if the authorization
was dropped, `DESTRUCTION_AUTHORIZATION_REQUIRED`. Active holds are
untouched by a supersession and keep blocking.

## Consequences

Easier: every destruction is explainable after the fact from three
records — the eligibility verdict's own reason code, the authorization's
version bindings, and the evidence's digest and executing authority. A
Legal Hold is a single object to place and to audit.

Harder: destruction takes three calls instead of one, and an operator who
shortens a retention schedule must re-authorize every affected record
rather than letting a job pick the change up. Both are intentional: the
extra steps are the control.

Also harder: `DestructionEvidence` is create-once, so an operational
mistake in the digest cannot be corrected in place — it would need a new,
separately-audited record under a future ADR. That is the correct trade
for evidence that must be trustworthy.

## Security impact

This ADR is where the pack's most consequential guarantee lives: an
active or indeterminate Legal Hold beats retention expiry, policy edits
and caller intent, at every step, including at execution time after
authorization has already been granted. The three-step workflow also
removes the single-call deletion primitive an attacker or a buggy job
would otherwise have.

The evidence record carries an opaque `evidence_digest` and no content,
so it cannot itself become a copy of the destroyed material (PACK-09
required invariant 13).

## Data impact

New schemas: `retention-policy`, `retention-start-event`,
`governed-record`, `legal-hold`, `destruction-authorization`,
`destruction-evidence`. New events:
`governed_record.retention_started`,
`governed_record.disposal_authorized`, `governed_record.destroyed`,
`legal_hold.status_changed`. No existing entity changes.

`GovernedRecord.record_version` is an optimistic-concurrency field;
`authorize_destruction` accepts an optional `expected_record_version` and
refuses on mismatch (`OPTIMISTIC_CONCURRENCY_CONFLICT`), matching the
pattern used elsewhere in the repository.

## Migration impact

None — no pre-existing retention or hold data exists. A future pack that
imports historical records must create a `RetentionStartEvent` for each
one; until it does, those records are simply not eligible for disposal,
which is the safe default.

## Reversibility

The three-step workflow is effectively irreversible as a design choice:
collapsing it back into a single delete would remove the audit trail this
pack exists to produce. The specific reason codes and the
`indeterminate` hold state are additive and could be extended without
breaking consumers.

## Related canon version

Canon `0.7.0`, no bump. Canon does not yet name `GovernedRecord`,
`RetentionPolicy` or `LegalHold` as canonical entities; they are
compliance-side control metadata owned by one service, and the four new
events use canon section 21's envelope unchanged. Elevating them to canon
entities would require its own amendment ADR.


## Amendment (Architecture & Domain Framework 0.8.1, same 0.9.0 round)

Framework section 11 adds two obligations this ADR did not carry.

**`RecordClass`.** Retention was previously bound to a record through a
`record_class` string plus a `RetentionPolicy`. The Framework requires a
record class to also fix its data classification, its custodian, its
disposition authority and its search/export eligibility, as one versioned
object. `domain.RecordClass` does that, and enforces one rule
structurally: the record owner may not also be the disposition authority.
Separating who owns a record from who may authorize destroying it is the
whole reason the class exists, and an owner authorizing destruction of
its own class is self-certification.

`search_export_eligibility` is the field a downstream pack needs before it
may index or export anything, and `no_index` is expressible — Framework
section 11 requires that some classes be excluded from general search
entirely, and a scheme with no way to say so would quietly index them.

**Hold propagation.** This ADR's Legal Hold blocks destruction of the
primary record. Framework section 11 observes that a hold which has not
reached the replicas, indexes, exports and backups derived from that
record is not an effective hold. `domain.HoldPropagationRecord` records
per-derivative state, and `assert_hold_propagation_resolved` refuses while
any known derivative is `unknown`, `pending` or `failed`.

One asymmetry is deliberate and is stated here rather than buried: an
**empty** propagation set is treated as resolved. PACK-09 can only reason
about derivatives it has been told about; it refuses on the ones it has,
and it cannot refuse on ones nobody registered. Propagation completeness
is therefore a deployment responsibility, not a guarantee this service
makes, and it is recorded as such in
`docs/handover/PACK-09-KNOWN-LIMITATIONS.md`.

`application.assert_destruction_propagation_resolved` is a **separate**
assertion rather than a new required argument on `authorize_destruction`.
Widening a command shipped earlier in this round would have broken its
callers for no gain; a deployment that participates in propagation calls
the assertion first, and one with no registered derivatives has nothing
to call it with. It checks every hold whose *scope* covers the record,
including released ones — a hold released before its export copy was
purged still leaves an unresolved derivative.
