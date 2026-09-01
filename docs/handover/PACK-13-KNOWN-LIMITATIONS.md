# PACK-13 — Known Limitations

**Round:** PACK-13 — candidate, then FINAL PASS after external CI
**Repository version:** `0.13.0` · **Canon version:** `0.8.0`

**PACK-13 FINAL PASS. EXTERNAL GITHUB ACTIONS PASS. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**

Every limitation below survived the PASS unchanged. A green pipeline
closes none of them, because not one of them is a defect the pipeline
could have found: they are boundaries of what a reference implementation
is.

This document exists because the honest description of what
`services/data-plane-service` is differs from what its name suggests, and
the difference is worth stating in full rather than discovering. Each
limitation below is a boundary of what was built, not a defect list: every
one is either the deliberate scope of a reference round, or a residual the
specification itself already recorded.

---

## 1. Every storage adapter is in memory. This is not a data plane.

The package is named for the production data plane and does not deploy
one. There is no PostgreSQL, no connection pool, no SQL, no cluster, no
replica and no broker anywhere in it. `storage.py` holds Python
dictionaries.

What that means precisely:

- **The contracts are real.** A production adapter implements the same
  `Protocol` and the domain layer does not change (`P13-PATH-001`).
- **The refusals are real and tested.** A grant-less migration is refused;
  a cross-domain write is refused; a stale expected version conflicts.
- **The enforcement is not.** A test proving that the code refuses a
  cross-domain write proves the code refuses it. It does not prove that a
  database grant would. `P13-DP-014`'s real enforcement is a per-domain
  role with no write grant outside its schema, and no such role exists
  here to inspect.

Every acceptance criterion whose stated evidence is a database grant
inventory, a live catalog snapshot, a role inventory or an egress-control
review is recorded as `deferred to production infrastructure` in the
acceptance matrix's implementation-status appendix — not as met.

## 2. `ReferenceUnitOfWork` is not a transaction

It buffers a state change and its outbox record and applies both on
commit, or neither on rollback. That is enough to make `P13-TX-003`'s
atomicity contract testable and it is emphatically not a transaction:
there is **no isolation, no durability and no recovery**. Two concurrent
commits of the same aggregate would both succeed, which a real database's
conditional update would prevent — `InMemoryAggregateVersionStore` says so
in its own docstring rather than implying otherwise.

The optimistic-concurrency _contract_ is what this round implements. Its
enforcement belongs where it can actually be enforced.

## 3. The identity guards are name-based, and a hash defeats them

`domain.GLOBAL_IDENTITY_KEYS` catches a payload key called `person_id`,
`email` or `member_id`. It does not catch a column called `ref_7` holding
an opaque hash of a person identifier, and
`idempotency.reject_identity_derived_key` cannot detect a key derived
from one by hashing.

This is the same residual `FIR-INV-001` has always carried: **behavioural
correlation is closed by no pack**, and a structural name check is a
backstop rather than the control. The control is the architecture — no
global person table, separate identifier lifecycles, no cross-domain
join — and this package's contribution is to make the obvious violations
impossible rather than the subtle ones detectable.

## 4. Canonicalization proves less than "the same schema"

Two documents with the same `content_digest` are byte-identical after
their format's own canonicalization, and nothing more. Two documents with
different digests may still mean the same thing, and the registry does not
adjudicate that (`P13-REG-005b`). `canonicalization.NOT_NORMALIZED`
enumerates what is deliberately not normalized.

The consequence a reader should carry away: a digest answers a narrow
content question, and `schema_version_id` answers a governance question.
Neither substitutes for the other, and the registry never merges them.

## 5. The compatibility checker is necessary and not sufficient

`compatibility.assess_structural_change` answers what a differ can see.
Six change classes — an enum's meaning, a reason code's semantics, an
event's meaning, identity linkage, retention semantics, legal effect — may
leave the serialized bytes identical while making every consumer wrong,
and no automated check will ever classify them.

The package escalates them to human review and refuses to proceed without
it. That is the correct behaviour and it is not detection: **a submitter
who does not declare a semantic-risk class gets a clean structural
verdict**, because nothing in the package can tell that the meaning
changed. The declaration is the control, and it is a human one.

## 6. The JSON Schema validator implements a small subset

Fixture validation uses `epd2_core.minimal_json_schema`, which supports a
deliberately small subset of JSON Schema. A schema using a keyword the
validator does not implement has that keyword **ignored**, not treated as
satisfied — the same honest limitation that module documents for itself.
`P13-REG-008`'s "examples validate against their schema" is therefore
weaker here than it will be against a full validator in CI.

## 7. No migration is ever executed

`MigrationService.execute` runs the gates, checks applied state, verifies
checksums and records the applied migration. It executes **no statement**,
because there is no database. `MigrationDefinition.statements` is an
opaque tuple of strings that nothing parses, and a real destructive
migration is deliberately absent from this repository.

Consequently: the dry-run evidence a plan carries is a _record_ that a
dry-run happened, not a rehearsal this round performed; and
`P13-MIG-008`'s batching and resume strategy is demonstrated by the
backfill runner rather than by a migration executor.

## 8. The broker is a double, and no topology is chosen

`delivery.ReferenceBroker` records what it was asked to publish and
returns whatever the caller configured. `BrokerPort` is the seam. No
transport provider, topic naming, partitioning or delivery guarantee of
any real broker is exercised, and `tests/test_boundaries.py` asserts that
no broker client is imported anywhere in the package.

For the voting domain this is not merely unfinished but **deliberate**:
`P13-VOTE-008` reserves broker topics, broker deployment arrangement,
connection-pool topology, service names, credential topology and
transport provider to PACK-15/16, taken with that pack's own threat
model. Choosing them here would settle a security architecture from
outside the pack that owns it.

## 9. Delivery is at-least-once, and duplicates are normal

Stated here because it is a limitation only in the sense that a reader
might have expected otherwise. The guarantee is **at-least-once delivery
with effectively-once consumer effect through idempotency**. Duplicates
are expected, counted and absorbed; they are not incidents. The stronger
phrase is claimed nowhere, and a scan over the package source enforces
that rather than a convention (ADR-072, `P13-DEL-002`).

## 10. Backup and restore do not exist, and the deletion gap stays open

A record deleted from a live database but present in backups **is not
deleted**. `retention.REFERENCE_BACKUP_STATEMENT` states this and states
that this reference implementation has no backups because it has no
durable storage — which is an _absence of the capability_, not a closure
of the gap. Closing it is **PACK-17's**, and `P13-BAK-011` forbids
claiming backup readiness without a restore test.

## 11. The administrative surfaces are contract-level, not an interface

`administration.py` holds typed view models with a payload guard. There is
no rendered surface, no route, no accessibility work and no frontend of
any kind: PACK-13 is not FRONT-PACK (`P13-FE-001`). `AC-P13-149`
(accessibility) is therefore `deferred to production infrastructure` with
FRONT-PACK named as the owner.

## 12. Reserved boundaries have no owner, and this round assigns none

The identity, eligibility, credential, voting, tally/result-certification,
communications, assemblies and candidacy boundaries are **conceptual
boundaries, not services**. The baseline contains reference-implementation
services for several of them (`identity-service`, `eligibility-service`,
`credential-service`, `voting-service`, `tally-service`); their existence
settles nothing about production data-plane ownership, and PACK-13 settles
nothing either (`P13-OWN-009`..`013`).

`AC-P13-163` — that whatever owner is later established complies with the
PACK-13 contracts — cannot be satisfied by this round, because the owner
does not exist. It is `blocked by PACK-14` and `blocked by PACK-15/16`.

## 13. The local verification run is incomplete — the external one is not

This build environment has **no network access to PyPI or npm**.
`make setup`, `uv sync --all-groups` and `npm install` cannot run, so every
Node-dependent stage of `make verify` — Prettier, ESLint, the TypeScript
typecheck, the TypeScript and frontend tests, the frontend build and the
browser, accessibility and visual-regression tests — cannot run here.

**That gap is now closed by the external run, not by an assertion.** The
GitHub Actions pipeline executed every stage and passed:
`docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION-RESULT.md` records the
figures, and `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log` is the
raw transcript, committed rather than summarised.

What remains true of _this_ environment is that the documentation changes
made after the green run were re-verified only by the deterministic checks
that run offline. `docs/handover/PACK-13-FINAL-PASS-REPORT.md` §10 states
which those were, and **no stage is reported as passing that did not
run.**

## 14. What this round is not

It **is** a PASS — an external pipeline verified the tree. It is not
production readiness. It is not legal activation, a compliance statement, a
procurement decision or a provider commitment. "PostgreSQL-compatible" is
an architectural direction recorded in ADR-069, not a vendor choice — and
no engine dependency exists anywhere in the repository to make it one.

The distance between those two sentences is the whole of this document.

---

## Cross-references

- `docs/packs/PACK-13/PACK-13-SPECIFICATION.md` — the normative source.
- `docs/packs/PACK-13/PACK-13-THREAT-MODEL.md` — the residual risks the
  specification round recorded; this round adds none and closes none.
- `docs/packs/PACK-13/PACK-13-ACCEPTANCE-MATRIX.md` — per-criterion
  status, including everything deferred to production infrastructure.
- `docs/handover/PACK-13-IMPLEMENTATION-CANDIDATE-REPORT.md` — what was
  built and what was verified locally, retained unchanged as the candidate
  round's own record.
- `docs/handover/PACK-13-FINAL-PASS-REPORT.md` — the round's closing
  report, including the external CI results.
- `docs/review/KNOWN_LIMITATIONS.md` — the repository-wide list.
