# `privileged-access-service` — PACK-12

Privileged administration, authorization-aware search, and governed data
export with DLP and statistical disclosure control.

**Status:** implementation candidate at repository version `0.12.0`.
Canon version unchanged at `0.8.0` — this round amends no canon.

**LOCAL VERIFICATION INCOMPLETE / EXTERNAL CI PENDING / NOT FINAL PASS**

`make verify` was never run end to end: the build environment cannot reach
PyPI or npm. Ruff, mypy and the repository-wide `pytest` suite passed;
every frontend stage, Prettier and the lockfile resolution did not run at
all. `uv.lock`'s new workspace-member entry was added by hand and has never
been accepted by `uv`. See
`docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md` §5 for exactly
which stages ran and which could not.

---

## Why one service for three contexts

`OD-P12-04` asked whether privileged administration, search and export
should be three deployables. They are not, and the reason is not
convenience.

They are one **control surface**. A privileged grant that could be
reasoned about without the search and the export it authorises is a
control in name only — the interesting question is never "may this person
hold this role" but "may this person, holding this role, run this query
and take this copy". Splitting them would put the answer to that question
across three audit paths and three idempotency stores, and `OD-P12-06`
forbids a second audit framework precisely because two records of one
fact are two records that can disagree.

So: one package boundary, one command frame, one audit path — and three
contexts separated by module, by aggregate and by role.

| Context                    | Aggregates                                                           | Roles that act in it                                                                         |
| -------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Privileged administration  | `PrivilegedAccessGrant`, `BreakGlassActivation`, `PrivilegedSession` | security/system administrator, IAM administrator, break-glass approver, independent reviewer |
| Authorization-aware search | `QueryAudit`, `IndexPolicy`                                          | security administrator (policy), any grant holder (queries)                                  |
| Governed export            | `ExportRequest`, `ExportArtifact`, `DisclosureRiskAssessment`        | data owner, export approver, DLP officer, disclosure-control reviewer                        |

---

## Module map

Each module imports only from those above it.

```text
exceptions      one class per registered reason code; no domain knowledge
domain          value objects, purpose, effective dating, prohibited payload keys
policy          the versioned numeric policy and its hard ceilings
classification  the canonical source → enforcement-tier mapping
roles           institutional roles consumed, operational assignments introduced,
                the incompatibility matrix, the authorization port
access          the grant aggregate and its lifecycle
breakglass      the separate emergency workflow
sessions        privileged sessions and the sealed, hash-chained evidence
search          index policy, query admission, execution
export          the export lifecycle, recipients, manifests, artifacts
dlp             controls, findings, assessment, transforms
disclosure      cohort policy, four rule families, release history
references      typed references exported and consumed
events          the forty-four canonical event builders
storage         storage ports and in-memory adapters — no delete method exists
application     the commands: one guard frame, one finish tail
```

---

## The command frame

Every state-changing command routes through one private `_guard` and one
private `_finish`. A guard a command can forget is a guard that is not in
force.

`_guard`, in this fixed order:

1. **Scope** — an undeterminable scope denies before any other check, any
   read and any write; the target record's scope is then re-asserted.
2. **Authority** — the presented authority object is resolved through
   `AuthorizationPort` to an active, effective-dated, scope-matching
   assignment. A `role_code` string is never proof. A command absent from
   `ACTION_REQUIREMENTS` denies rather than defaulting open.
3. **Role incompatibility and institutional escalation** — re-checked at
   the moment of the act against the roles the actor _really_ holds.
4. **Self-approval and separation of duties** — every prior actor the
   command names is compared with the acting one.
5. **Purpose** — where declared, it must be one the resolved role serves.
6. **Idempotency** — the caller supplies `event_id`; a replay returns the
   recorded aggregate, a reuse with different content raises.
7. **Optimistic concurrency** — after idempotency on purpose: a true
   replay must not fail on a version the first execution advanced past.

`_finish` appends to Audit Core, publishes the envelope, and only then
records the idempotency row. **Audit before event**: an event that escaped
without an audit row is an unaccountable act, and the reverse ordering is
what produces one.

Where the Event Catalog names several events for one atomic act — a
search is submitted, authorized, executed and partly suppressed —
`_finish` takes an ordered sequence of emissions. The first carries the
command's own `event_id`; the rest carry deterministic `uuid5` identifiers
derived from it, so a replay produces byte-identical audit rows that
`append_audit_event` recognises rather than duplicating.

---

## Five things that are structural, not documented

**No bypass exists.** There is no feature flag, environment switch,
deployment mode, privileged grant or emergency path that disables any
invariant, audit append or separation check. `roles.NO_BYPASS_NOTE` says
so and no code path contradicts it. Emergency access is a _separate_
workflow that only ever adds obligations — a second approver, a
notification, a shorter ceiling, an independent review.

**No standing superuser is expressible.** `EffectiveWindow` has no
"no end" option, so an unbounded grant is not constructible rather than
merely discouraged. There is no `renew` method: continued access costs a
fresh decision.

**No universal console and no all-domain role.** No role set, in any
combination and under any emergency condition, reaches ballot content or
mutates an audit record. Holding every privileged role at once is refused
by the incompatibility matrix.

**No deletion.** No storage port defines a delete-shaped method, with one
named exception: `SearchIndexStore.remove`, which requires
`IndexRemovalEvidence` naming the PACK-09 or PACK-11 decision it followed.
Removing a record from the index is not deleting the record.

**No voting reference type is declared.** `references.py` has types for
documents, evidence bundles, publication renditions, legal holds and
retention bindings — and nothing for ballots, votes or tallies. A caller
cannot reach for a type that was never defined.

---

## Honest limits

- **Tamper-evident, not tamper-resistant.** The session hash chain makes
  alteration _detectable_; nothing here prevents it, and without an
  external anchor that is the whole of what `FIR-INV-010`-style integrity
  buys.
- **A watermark marks a copy; it does not stop one being made.**
- **Export revocation withdraws authorization** and blocks further
  platform-mediated access. It does not retrieve a copy already delivered,
  and nothing in this package says it does.
- **A destruction attestation is a recipient's statement**, not a verified
  fact. This platform cannot observe a third party's storage.
- **Every adapter is in-memory.** No production database, no real event
  bus, no external IAM or IdP, no MFA, no HSM or PKI, no production search
  engine, no production DLP provider, no incident-response platform, no
  external recipient portal, no frontend.
- **No legal claim.** Nothing here establishes that a privileged act was
  lawful, that an export satisfied a legal basis, that a disclosure
  control met a statistical authority's standard, or that any of it is
  admissible.

See `docs/handover/PACK-12-KNOWN-LIMITATIONS.md`.

---

## Running the tests

From the repository root:

```bash
uv run pytest services/privileged-access-service/tests
uv run ruff check services/privileged-access-service
uv run mypy services/privileged-access-service
```
