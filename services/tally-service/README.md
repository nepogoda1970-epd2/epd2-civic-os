# Tally Service

Owns `Tally` (canon section 15.5) and `ResultPublication` (canon section
15.6). `docs/adr/ADR-005-pack-03-service-decomposition.md` item 5
consolidates the canon-named "Tally Service" and "Result Publication
Service" into this one physical package: a `ResultPublication`'s aggregate
counts are a published view of the same completed `Tally`, and canon
gives no reason a work-in-progress tally needs an independent owner from
its eventual publication.

## No PACK-03↔PACK-03 import (ADR-008 item 3) — the central boundary consequence

Conceptually, a tally consumes `voting-service`'s validated `VoteEnvelope`
set. **This package never imports `epd2_voting_service`, or any other
PACK-03 sibling package, anywhere in its source** — enforced structurally
by `tests/test_application.py::test_package_never_imports_epd2_voting_service`
and `test_package_only_depends_on_epd2_core_and_audit_core` (AST-walk
checks over every `.py` file, not a docstring promise).

ADR-008 item 3, verbatim:

> **Forbidden regardless of direction**: any PACK-03↔PACK-03 import across
> the six new services (each communicates with its siblings only through
> the canonical events in `docs/handover/PACK-03-SPEC.md` section 5, or a
> specific, named, whitelisted read function — e.g. `tally-service`
> reading `voting-service`'s validated `VoteEnvelope` set requires its own
> named interface function, never free access to `voting-service`'s
> internals).

That named interface function does not exist yet — ADR-008 item 1
explicitly lists `tally-service` (along with `deliberation-service`,
`moderation-service`, `delegation-service`) as having "no PACK-02
dependency identified yet," and item 3 makes a PACK-03↔PACK-03 edge to
`voting-service` require its _own_ future ADR, not something this task
may invent informally.

**Practical consequence**: every command in `application.py` that would
conceptually need real vote data instead accepts it as **plain
parameters** — `int`s and `Mapping[str, int]`s — supplied by whatever
service or orchestration layer wires `voting-service` and `tally-service`
together:

- `start_tally` takes `input_set_hash: str` (pre-computed by the caller,
  optionally via `domain.compute_input_set_hash` — see below) and
  `algorithm_version: str`, never a real `VoteEnvelope` collection.
- `complete_tally` takes `result_data: Mapping[str, int]` and
  `invalid_vote_count: int` — the caller has already counted votes per
  option; this service never counts a raw `VoteEnvelope` itself.
- `publish_result` takes `eligible_count`, `credential_count`,
  `accepted_vote_count`, `rejected_vote_count`, `quorum_threshold`, and
  `option_counts` all as plain parameters — the caller has already read
  the real `Ballot`'s `quorum_rule`/`challenge_window_hours` and resolved
  them to concrete values (an absolute vote-count threshold; an integer
  hour count) before calling here.

This is a **deliberate architectural consequence of ADR-008, not an
oversight or a missing feature**. `domain.compute_input_set_hash` exists
precisely so a caller has a documented, deterministic way to build
`input_set_hash` from `(vote_envelope_id, choice)` pairs it already read
from `voting-service`'s own `application` layer, without this package
ever needing to import anything from `epd2_voting_service` to do so.

## Tally verification-status machine (canon section 15.5)

```
pending -> running
running -> completed
running -> verification_failed
completed -> verified
completed -> verification_failed
verification_failed -> running
verified -> superseded
```

All seven edges are implemented structurally in `domain.ALLOWED_TRANSITIONS`
(so CT-00-02/CT-00-03-style tests can validate the full graph), but only
four public `application.py` commands are exposed, mapped from canon
events section 20.10's tally/result subset:

| Command          | Transition                                                        | Event                                |
| ---------------- | ----------------------------------------------------------------- | ------------------------------------ |
| `start_tally`    | `pending -> running` (created already-running)                    | `tally.started`                      |
| `complete_tally` | `running -> completed`                                            | `tally.completed`                    |
| `verify_tally`   | `completed -> verified` **or** `completed -> verification_failed` | `tally.verified` (success path only) |
| `publish_result` | (reads a `verified` `Tally`, creates `ResultPublication`)         | `result.published`                   |

**`verify_tally`'s failure path emits no canonical event.** Canon events
section 20.10 names no `tally.verification_failed` event — only
`tally.verified`. A failed verification (`completed -> verification_failed`)
is persisted and audited (`reason_code = INTEGRITY_CHECK_FAILED`, canon
section 24) exactly like every other state-changing command (CT-00-07),
but `VerifyTallyResult.event` is `None` on that path — see
`application.verify_tally`'s docstring and
`tests/test_application.py::test_verify_tally_failure_emits_no_event_but_audits_integrity_check_failed`.

**`verification_failed -> running` (retry) and `verified -> superseded`
are structural-only.** Neither has a corresponding public command, since
canon's own event list gives no event name for a tally "retry" or
"supersede" action. They exist in `domain.ALLOWED_TRANSITIONS` (and are
exercised by `tests/test_domain.py`'s full-transition-table
parametrization) purely so the state machine is complete and testable —
mirroring `docs/adr/ADR-009-voting-delegation-quorum-defaults.md` item
14's precedent (`voting-service`'s `BallotStatus.INVALIDATED`) of
implementing a canon status/transition structurally without necessarily
exposing a command that reaches it.

## Tie handling — no silent tie-break (ADR-009 item 11, accepted, binding)

ADR-009 item 11, verbatim:

> **How are ties handled?** Proposed: no silent tie-break. A tied result
> is recorded as its own explicit `ResultPublication` outcome (e.g.
> `threshold_result = "tie_no_decision"`); any specific tie-break method
> must be an explicit, documented, per-ballot `threshold_rule`
> configuration — never an implicit fallback baked into tally logic.

`domain.ThresholdResult` is a `StrEnum` with exactly `THRESHOLD_MET =
"threshold_met"`, `THRESHOLD_NOT_MET = "threshold_not_met"`,
`TIE_NO_DECISION = "tie_no_decision"`. `domain.compute_threshold_result`
detects a tie between the leading options (two or more options sharing
the strictly-highest vote count) and returns `TIE_NO_DECISION` — **never**
an arbitrarily-chosen winner, regardless of what fraction of the total
that count represents. `THRESHOLD_MET` additionally requires the sole
leading option to hold an absolute majority (`count * 2 > total`), not
merely a plurality — a three-way split where the leader has 40% of the
vote is `THRESHOLD_NOT_MET`, not a false "met".

`tests/test_domain.py::test_compute_threshold_result_tie_is_tie_no_decision`
and `tests/test_application.py::test_publish_result_tie_produces_tie_no_decision_and_classification_code`
are the dedicated proofs that a tied `result_data` produces
`tie_no_decision`, both at the pure-function level and end-to-end through
`publish_result`.

## Quorum is optional per ballot (ADR-009 item 5, accepted)

ADR-009 item 5, verbatim:

> **Is quorum required for every procedure?** Proposed: no.
> `Ballot.quorum_rule` is already an optional, per-ballot field; default to
> no quorum requirement unless a specific ballot configures one.

`publish_result` accepts `quorum_threshold: int | None`. `domain.QuorumResult`
is a `StrEnum` with exactly `QUORUM_MET = "quorum_met"`, `QUORUM_NOT_MET =
"quorum_not_met"`, `NOT_REQUIRED = "not_required"`. When `quorum_threshold`
is `None`, `domain.compute_quorum_result` returns `NOT_REQUIRED`
unconditionally — it never compares against `accepted_vote_count` at all
in that case. Only when a caller supplies a concrete threshold (already
resolved from the real `Ballot.quorum_rule`, which this service cannot
read — ADR-008) does the function compare `accepted_vote_count` against
it and return `QUORUM_MET`/`QUORUM_NOT_MET`.

## Non-finality guarantee (ADR-010, canon 0.2.0 addition) — read this carefully

Canon section 15.6, verbatim (Russian original, this ADR's own canon
edit):

> `challenge_deadline_at` вычисляется как `published_at` плюс применимый
> `challenge_window_hours` связанного Ballot (либо default, если поле не
> задано). Наступление `challenge_deadline_at` — необходимое, но не
> достаточное условие окончательности результата: до появления
> канонического либо отдельно утверждённого механизма регистрации и
> рассмотрения технических возражений (technical challenge)
> ResultPublication остаётся в состоянии ожидания окончательности на
> уровне прикладной логики. Ни один модуль не вправе автоматически
> считать результат окончательным исключительно по факту истечения
> `challenge_deadline_at`.

ADR-010's Owner decision amendment, verbatim:

> - Expiry of `challenge_deadline_at` is **necessary, but not by itself
>   sufficient**, for finality.
> - PACK-03 must not automatically declare a `ResultPublication` final
>   merely because the deadline elapsed.
> - Until a canonical or explicitly approved technical-challenge
>   registration and adjudication mechanism exists, `ResultPublication`
>   remains in a provisional/finality-pending state **at the application
>   level**.
> - No hidden, pack-local challenge process may be invented to fill this
>   gap informally.
> - The future challenge mechanism (registration and adjudication) must be
>   introduced through its own ADR before real production finality can
>   ever be enabled.

`publish_result` computes `challenge_deadline_at = published_at +
effective_challenge_window_hours` (`domain.compute_challenge_deadline`),
where the effective window is the caller-supplied `challenge_window_hours`
if given, else this service's own `DEFAULT_CHALLENGE_WINDOW_HOURS = 72`
(mirroring `voting-service`'s identical constant — duplicated
intentionally, since ADR-008 item 3 forbids the PACK-03↔PACK-03 import
that could otherwise let the two services share one literal).

`domain.compute_finality_state(result, now)` returns a
`domain.FinalityState`, a `StrEnum` with **exactly two members**:
`PROVISIONAL_BEFORE_DEADLINE = "provisional_before_deadline"` (when `now <
challenge_deadline_at`) and `PROVISIONAL_PENDING_CHALLENGE_MECHANISM =
"provisional_pending_challenge_mechanism"` (when `now >=
challenge_deadline_at`). **There is deliberately no third member meaning
"final"**, and no code path anywhere in this service — not in `domain.py`,
not in `application.py` — ever returns or claims a final state, no matter
how far `now` is past the deadline.

`tests/test_domain.py::test_finality_state_has_exactly_two_values_neither_meaning_final`
asserts `"final" not in {v.value for v in FinalityState}` directly, and
`test_compute_finality_state_long_after_deadline_never_implies_finality`
calls `compute_finality_state` with `now` a full 3650 days (ten years)
past `challenge_deadline_at`, asserting the result is still
`PROVISIONAL_PENDING_CHALLENGE_MECHANISM` — never anything implying
finality. **A future, separate ADR must introduce the actual
challenge-registration-and-adjudication mechanism before this service (or
any other) may ever compute a real "final" state for a `ResultPublication`.**

## Bookkeeping fields threaded through to `ResultPublication`

Canon section 15.6 lists `eligible_count`, `credential_count`,
`accepted_vote_count`, `rejected_vote_count` as `ResultPublication`
fields directly (not `Tally` fields) — so this service's own judgment call
is to thread them through `publish_result`'s own parameter list as plain
caller-supplied `int`s, rather than adding them as additive bookkeeping
fields on `Tally` itself. `Tally` therefore carries exactly canon section
15.5's field list, unmodified; `ResultPublication` carries exactly canon
section 15.6's field list, unmodified (plus `challenge_deadline_at`, the
ADR-010 addition already part of canon). No pack-additive field exists on
either dataclass.

## Identity separation (ADR-009 item 15)

ADR-009 item 15, verbatim:

> **What audit-package data is published openly?** Proposed:
> `ResultPublication`'s aggregate counts (`eligible_count`,
> `credential_count`, `accepted_vote_count`, `rejected_vote_count`,
> `quorum_result`, `threshold_result`) plus a redacted audit-chain proof
> (hashes only, never full `AuditEvent` payloads) — never individual
> `VoteEnvelope` contents or anything identity-linked.

`domain.FORBIDDEN_FIELD_NAMES = frozenset({"account_id", "person_id",
"identity_record_id"})` applies to **both** `Tally` and
`ResultPublication` — neither dataclass may ever carry one of these
fields, or any individual vote content. `tests/test_domain.py`'s
`test_tally_has_no_forbidden_identity_field` and
`test_result_publication_has_no_forbidden_identity_field` are the
structural proofs, mirrored in style exactly from
`epd2_voting_service.domain.FORBIDDEN_FIELD_NAMES`.

## Reason codes

Canon section 24 codes reused verbatim: `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`,
`PERMISSION_DENIED`, `INTEGRITY_CHECK_FAILED` (used for
`completed -> verification_failed`).

Additive, this service's own documented codes:

- `TALLY_QUORUM_NOT_MET` — audit-success classification code for a
  `publish_result` call whose computed `quorum_result` is
  `QUORUM_NOT_MET`. Not an error: `publish_result` still succeeds and
  still creates the `ResultPublication`; this only marks _why_ in the
  audit trail.
- `TALLY_THRESHOLD_TIE_NO_DECISION` — the same idea for a tied result
  (`threshold_result == TIE_NO_DECISION`). Takes priority over
  `TALLY_QUORUM_NOT_MET` if both conditions hold simultaneously (see
  `application._publish_result_reason_code`).
- `TALLY_STATUS_CHANGED` — generic info-severity classification for
  `start_tally`/`complete_tally`/a successful `verify_tally`.
  `RESULT_PUBLISHED` — the default classification for `publish_result`
  when neither of the two conditions above applies.
- `TALLY_RECORD_CONFLICT` / `RESULT_PUBLICATION_RECORD_CONFLICT` —
  storage-level idempotency-vs-conflict codes (CT-00-04), following the
  exact precedent already established by `credential-service`'s
  `CREDENTIAL_DUPLICATE_ISSUANCE_CONFLICT` and `eligibility-service`'s
  `ELIGIBILITY_RULE_VERSION_FROZEN`.

## `input_set_hash` construction

`domain.compute_input_set_hash(vote_records)` takes an iterable of
`(vote_envelope_id, choice)` pairs and returns a sha256 digest over their
canonically-serialized, **sorted** representation
(`epd2_core.canonical_json.canonical_dumps`), mirroring
`epd2_eligibility_service.domain.compute_snapshot_digest`'s exact
determinism style — sorting first makes the digest independent of
collection/iteration order, so two calls built from the same logical vote
set always match. This service never has a real `VoteEnvelope` to hash
directly (ADR-008 item 3); the caller that wires `voting-service` and
`tally-service` together is responsible for reading the real, validated
`VoteEnvelope` set and passing its `(vote_envelope_id,
encrypted_or_encoded_choice)` pairs into this function before calling
`application.start_tally` with the resulting digest.

## Idempotency (CT-00-04)

Every command accepts an optional `event_id: UUID | None` — a caller
retrying an exact command should pass the same `event_id` it used on the
original attempt so both the stored entity and the audit trail converge
on the same single record rather than duplicating on retry. Storage-level
`create` calls (`TallyStore.create`, `ResultPublicationStore.create`) are
separately idempotent by primary id + content equality, raising
`TallyRecordConflictError`/`ResultPublicationConflictError` only when a
repeated id carries genuinely different content.
