# CTRL-01 — Governed Control Plane & Authority Operations Foundation

> **CTRL-01 C1 canonical reconciliation — 2026-09-02.** This candidate is
> reconciled to canonical `main@217559b7f21c338d6fe8d4e4676082cd3840251c`. P1 statements that API-05,
> INFRA-02 or OPS-02 were not accepted are historical and superseded for current-state
> interpretation. Their exact accepted governance records are bound by Git blob identity.
> API-06 remains `NEXT / NOT ACCEPTED`; the API layer remains open and System Trial
> Preview remains `CHECKPOINT_NOT_OPEN`. This bounded CTRL-01 acceptance does not claim
> `overall CTRL-layer closure`, production readiness, legal activation, or BSI/Common Criteria certification.


**Stage mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`
**Self-state:** `CTRL01_IMPLEMENTATION_COMPLETE / LOCAL_VERIFICATION_PASS / PRESEAL_READY / NOT_ACCEPTED`

This stage opens and closes no canonical layer. It makes no claim of CTRL
acceptance, CTRL closure, production readiness, final security acceptance,
BSI/Common Criteria certification or legal activation.

## 1. What this stage is

CTRL-01 turns the governed authority model into an executable, testable
administrative action model. The governing requirements are `FIR-CTRL-001`
(unified control plane), `FIR-GOV-004` (regional authority suspension and
intervention), `FIR-GOV-005` (statutory party-organ competence and digital
authority binding), `FIR-SEC-004` (access, credential and key authority
lifecycle) and `FIR-TRUST-002`/`FIR-TRUST-003` (resilient trust, key classes and
crypto-agility).

The single design rule everything else follows from:

```text
authority = exact subject
          + exact office/role
          + exact organizational scope
          + exact capability
          + exact governing rule version
          + exact source decision
          + a validity window
          + a current lifecycle state
```

Any unresolved element is a refusal, not a default-permit.

## 2. Where it lives

| Path | Contents |
| --- | --- |
| `services/control-plane-service/src/epd2_control_plane_service/` | the implementation |
| `services/control-plane-service/tests/` | the packaged suites |
| `scripts/ctrl01_validator.py` | the twenty-two governed gates |
| `scripts/ctrl01_registry_export.py` | generator for the control-plane registry |
| `scripts/system_trial_preview_prepare.py` | the System Trial Preview harness |
| `docs/ctrl/CTRL-01/EPD2_Control_Plane_Registry.csv` | the `FIR-CTRL-001` registry (generated) |
| `validation/ctrl01/` | preseal evidence |
| `validation/system_trial_preview/` | trial preparation artifacts |

## 3. Module map

| Module | Responsibility |
| --- | --- |
| `domain.py` | authority, scope, session, credential, key reference, restriction, supervision, break-glass and action types |
| `policy.py` | the governed enforcement obligations, and the switches the mutation suite flips |
| `inventory.py` | the administrative action inventory (W1) and the `NO_UI` decisions |
| `authority.py` | authority source journal and read models (W2) |
| `sod.py` | the separation-of-duties matrix (W3) |
| `intervention.py` | bounded regional intervention, levels 1–4 (W4) |
| `breakglass.py` | the emergency lifecycle (W6) |
| `application.py` | request → approve → execute with commit-time reauthorization (W7, W9) |
| `api.py` | control-console API contracts (W7) |
| `audit.py` | privacy-safe, hash-chained, append-only evidence (W10) |
| `verification.py` | the shared governed check suite |
| `mutations.py` | the anti-cheat corpus (W11) |
| `freeze.py` | same-bytes preseal identity |
| `reference_world.py` | the deterministic governed fixture used by both the tests and the validator |

## 4. The hard constraints, and how each is enforced

| Constraint | Enforcement | Proof |
| --- | --- | --- |
| No `admin = everything` | no action carries the full right set; no authority may hold every *mutating* action code, or every right except review | `CHK-NO-UNIVERSAL-ADMIN`, `MUT-01` |
| No implicit Bund takeover | `Scope.contains` is exact-match; an oversight grant is honoured only when it equals the single scope its source decision names, so both widening and re-pointing fail closed | `CHK-SCOPE-ISOLATION`, `CHK-NO-IMPLICIT-BUND-TAKEOVER`, `MUT-02`, `MUT-19`, `MUT-33` |
| No hidden operator bypass | platform scope carries no governance action code; actor classes are disjoint | `CHK-PLATFORM-GRANTS-NO-POLITICAL-AUTHORITY`, `CHK-ACTOR-CLASS-SEPARATION` |
| Voting boundaries not weakened | voting-domain key references are refused to every control right; no action may sit inside the voting domain (rejected at inventory construction) | `CHK-VOTING-BOUNDARY`, `MUT-22`, `MUT-23` |
| No persistent voting identifier for admin convenience | evidence attributes are screened before write | `CHK-PRIVACY-MINIMIZATION`, `MUT-21` |
| Rights remain separable | nine-rule SoD matrix evaluated at commit | `CHK-SELF-APPROVAL-REJECTED`, `CHK-SECRET-VISIBILITY-SEPARATION` |
| Emergency authority narrow and expiring | absolute expiry from activation; no renewal transition exists | `CHK-EMERGENCY-EXPIRY`, `CHK-EMERGENCY-NOT-RENEWABLE`, `MUT-10`, `MUT-11` |
| History never rewritten | append-only hash chain plus an append-time (count, head) anchor held outside the record list, recomputed independently of policy | `CHK-EVIDENCE-IMMUTABLE`, `MUT-15`, `MUT-16`, `MUT-16B`, `MUT-16C`, `MUT-17` |
| Fail closed on unknown authority state | unknown action, unknown session, unknown principal and unknown request parameter all refuse | `CHK-FAIL-CLOSED-ON-UNKNOWN`, `CHK-NO-MASS-ASSIGNMENT`, `MUT-18`, `MUT-25` |
| No legal or final security claim | forbidden self-state scan over the packaged files | `CHK-SELF-STATE-BOUNDED`, `MUT-30`, gate G21 |

## 5. Authorization flow

```text
submit_request  ->  actor class, session, credential, voting boundary,
                    REQUEST right, active restrictions
approve         ->  actor class, session, self-approval, duplicate approver,
                    APPROVE right, secret-visibility separation
execute         ->  actor class, session, credential, voting boundary,
                    EXECUTE right (or a bounded break-glass grant),
                    active restrictions, quorum,
                    re-resolution of EVERY approver's authority,
                    separation of duties
                ->  immutable evidence
```

Authorization happens twice by construction. `execute` re-resolves the executor
*and every approver* against the state at commit time; it never reuses the
request-time decision. For the executor this covers authority, scope, session,
credential and restriction state; for each approver it covers authority, the
authority identity the approval was given under, credential state and active
restrictions. Approver *session* state is not re-checked at commit — an approver
does not act at commit time — and that boundary is deliberate rather than
overlooked.

Eight time-of-check/time-of-use cases are covered by
`tests/test_commit_time_reauthorization.py`, including a baseline control case
that commits successfully when nothing changed — without it, a workflow that
never commits would score a perfect TOCTOU result.

Request parameters are constrained to a small governed allow-list
(`PERMITTED_REQUEST_PARAMETERS`); an unrecognised key is refused rather than
stored, so there is no field a caller can smuggle onto an authority record.

## 6. Regional intervention

Four levels, and deliberately no fifth:

1. `SESSION_QUARANTINE` — technical containment. Not a removal from office.
2. `AUTHORITY_SUSPENSION` — one exact `OrganizationalAuthority`.
3. `REGIONAL_ACTION_RESTRICTION` — named action codes in one exact scope.
4. `TEMPORARY_SUPERVISION` — narrow functional substitution, capped at 90 days.

There is no `region_disabled` member of `InterventionType`, and
`open_restriction` validates every action code against the governed inventory,
so a caller cannot freeze "everything" by passing a wildcard, an unknown code or
an empty set. Every temporary intervention carries a mandatory `valid_until`
enforced at construction, and extension produces a *new* decision that supersedes
the old restriction — there is no in-place prolongation.

Seven member and regional capabilities are preserved against any intervention
that lacks its own competent legal decision; `assert_continuity` refuses a
proposed intervention that reaches them.

## 7. Evidence

Every consequential act **and every refusal** appends a record carrying actor
reference, authority basis, action, scope, object, time, result, reason code,
approval references and a correlation reference. The chain is
`sha256(canonical(record) + previous_hash)`, and `append` additionally maintains
an anchor — the record count and head hash — held outside the record list.

The anchor is what makes the chain honest. A walk over the stored records alone
cannot see two realistic tampering shapes: deleting the newest record, and
rewriting a record while recomputing every hash forward. Both leave an
internally perfect chain, and both disagree with the anchor.

The journal exposes `append`, `anchor`, `records`, `head_hash`, `find`, `verify`
and `export` and nothing else. There is no update and no delete, public or
private: the tampering helpers the mutation corpus needs live in `mutations.py`,
in the attacker model, so the packaged evidence module ships no history-rewrite
primitive.

Attributes are screened *before* the write. A voting-linkable identifier, a
secret-shaped field name, raw key material or an oversized payload is refused
rather than written and filtered later.

## 8. The mutation corpus

Thirty-seven mutations across five kinds — removing an enforcement, corrupting
data, weakening the inventory, changing the runtime, and lying in the packaging.
Each declares the check expected to catch it, and the suite asserts both that it
is detected *and* that the expected check is the one that caught it. The
governed baseline is asserted to pass every check, and every check is asserted to
be breakable by at least one mutation — a check no mutation can break proves
nothing.

Two properties of the corpus are worth stating plainly, because they are the
ones that decay first. A mutation must model the defect it names rather than
some easier neighbour: `MUT-18` drives a real parameter-injection path through
the runtime, and `MUT-29` hands the freeze check a recorded manifest that
disagrees with the bytes on disk, so both are measurements rather than
assertions handed their own answer. And a check must isolate the property it
claims: `check_self_approval` uses a principal holding *both* the request and
approve rights, `check_commit_time_reauthorization` revokes an approver rather
than the executor, and `check_no_implicit_bund_takeover` probes the one
principal in the fixture that actually holds an oversight grant. Each of these
was, at one point in this stage's development, the weaker version — an
independent review found them, and the fixtures were changed.

## 9. What CTRL-01 deliberately does not do

- It opens no CTRL layer and closes nothing.
- It imports no code from the accepted API candidates: those runtimes live in
  sealed candidate archives, not in this working tree, so CTRL-01 binds to their
  accepted governance semantics by reference and any later integration must
  re-derive those bindings against the exact accepted bytes.
- It resolves no governance conflict on its own authority. Conflicts observed in
  the canonical register are recorded in `validation/ctrl01/dependency_reconciliation.json`
  for governed reconciliation, per `EPD2_PROJECT_ENTRYPOINT.md` section 3.
- It claims nothing about API-05, API-06, INFRA-02 or OPS-02, none of which is
  accepted.

## 10. Reproducing the result

```sh
uv sync --all-groups
uv run python scripts/ctrl01_registry_export.py
uv run python scripts/system_trial_preview_prepare.py
uv run pytest services/control-plane-service/tests -q
uv run python scripts/ctrl01_validator.py
```

G22 compares the packaged files against the manifest recorded in
`validation/ctrl01/freeze_manifest.json` by a previous run — it is read from disk
before this run computes anything, so the comparison is against a prior freeze
rather than against itself. On a tree with no recorded baseline the gate records
one and says so. After a deliberate source change, re-record with
`--record-freeze`; without that flag a changed packaged file fails G22, which is
the same-bytes rule doing its job.

The validator's terminal marker is `CTRL01_RESULT:<PASS|FAIL>:<path>` and its
exit code is 0 only when all twenty-two mandatory gates pass. No gate may report
`SKIPPED`, `NOT_RUN` or `ASSUMED_PASS`; a gate that cannot run is a failure.

## 11. Before any future seal

1. Re-fetch current `main` and re-run G01. A drifted baseline is a reconciliation
   obligation, not a formality.
2. Reconcile the exact accepted identity of API-05 and API-06, or record each
   explicitly as not yet accepted.
3. Reconcile INFRA-02 and OPS-02 if either is accepted by then.
4. Re-read the Program Control Register and the Master Future Implementation
   Register.
5. Re-run every affected gate after any predecessor delta.
6. Freeze under the same-bytes rule:
   `tested bytes == verified bytes == frozen bytes == packaged bytes`.
