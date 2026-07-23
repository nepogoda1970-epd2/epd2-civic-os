# ADR-010: Canon minor-version addition — Ballot challenge window and ResultPublication finality fields

## Status

`accepted`, with an amendment clarifying finality (see Owner decision).

## Date

2026-07-22

## Owner decision

Accepted with amendment, 2026-07-22. The two proposed canon additions
(Decision items 1 and 2, below) are accepted exactly as proposed:

1. `Ballot.challenge_window_hours` — optional integer; repository default
   72 hours; configurable per ballot.
2. `ResultPublication.challenge_deadline_at` — calculated from
   `published_at` plus the applicable challenge window.

The owner additionally required an explicit finality clarification,
which this ADR now records as part of its Decision (not left to
implementation-time judgment):

- Expiry of `challenge_deadline_at` is **necessary, but not by itself
  sufficient**, for finality.
- PACK-03 must not automatically declare a `ResultPublication` final
  merely because the deadline elapsed.
- Until a canonical or explicitly approved technical-challenge
  registration and adjudication mechanism exists, `ResultPublication`
  remains in a provisional/finality-pending state **at the application
  level** (this ADR does not add a canonical `finality_status` field —
  see Decision's "deliberately not proposed" note, which this amendment
  leaves unchanged in that respect).
- No hidden, pack-local challenge process may be invented to fill this
  gap informally.
- The future challenge mechanism (registration and adjudication) must be
  introduced through its own ADR before real production finality can ever
  be enabled.
- Contract tests may verify `challenge_deadline_at`'s calculation and the
  provisional-window behavior itself, but must not claim, assert, or rely
  on end-to-end challenge adjudication or automatic finality — there is
  no such mechanism yet to test.

Per this task's own instruction and this project's standing canon-
immutability rule, the canon edit implementing Decision items 1–2 (and
this finality clarification, recorded in the canon text itself — see
canon sections 15.1/15.6) has now been performed as part of this
acceptance, since this specific task is the "separate, dedicated task"
`docs/canonical/README.md`'s own rule requires, combined with this ADR
reaching `accepted`. Canon version moved `0.1.0 → 0.2.0`:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  5ed52c3a6a94e821323616ac369595fd364a71115cf5c1c6763d8edb51a6044a
CANON_VERSION = 0.2.0
```

## Context

`docs/adr/ADR-009-voting-delegation-quorum-defaults.md` item 13 (accepted
with amendment, 2026-07-22) requires: a technical-challenge deadline
defaulting to 72 hours, configurable per ballot; `ResultPublication`
remaining provisional until that window elapses without an accepted
integrity challenge. The owner explicitly rejected deferring the
required canon change to an unspecified future ADR — this ADR is that
change, prepared now, through the canon's own minor-version process
(canon section 25).

Canon version `0.1.0`, as it stands, gives `Ballot` (section 15.1) no
field expressing a configurable challenge window, and gives
`ResultPublication` (section 15.6) no field expressing when it stops
being provisional. This is different in kind from every additive change
this project has made so far: PACK-02's 21 additive reason codes
(ADR-004) and PACK-03's own planned additive reason codes (ADR-006) were
both handled through pack-level registry files specifically so the canon
itself would never need editing for that kind of addition. A challenge
window and a finality cutoff are not reason codes — they are properties
of the canonical entities `Ballot` and `ResultPublication` themselves, so
no non-canon registry file can add them; only the canon document can.
This is therefore the first ADR in this project proposing an actual edit
to `docs/canonical/TZ-00-domain-event-canon.md`'s text, not merely to a
pack-level artifact that depends on it.

## Problem

Without a canonical field, "the challenge window" and "provisional vs.
final" have nowhere authoritative to live. Any PACK-03 implementation
would either invent an undocumented, pack-local field on `Ballot`/
`ResultPublication` (silently diverging from what the canon says those
entities contain — exactly the kind of undocumented deviation canon
section 26 exists to prevent) or hard-code a single global constant with
no configurability, contradicting the owner's explicit "must be
configurable per ballot" requirement.

## Considered options

- Option A — add the two fields directly to `Ballot` (section 15.1) and
  `ResultPublication` (section 15.6) as a canon minor version (`0.1.0 →
0.2.0`), following canon section 25's own definition of a minor change
  ("добавление обратно совместимой сущности, поля, события или статуса" —
  addition of a backward-compatible entity, field, event, or status).
- Option B — avoid a canon edit entirely by modeling the challenge window
  as a PACK-03-local configuration object outside the canon (e.g. a
  `voting-service`-only `BallotPolicy` record never referenced by the
  canon), keeping it a pack-level convention rather than canonical data.
- Option C — do nothing now; continue deferring the field to an
  unspecified future ADR. Already explicitly rejected by the owner in
  the ADR-009 acceptance.

## Decision

Option A, accepted with the finality amendment recorded in Owner decision
above. Canon minor-version bump `0.1.0 → 0.2.0`, now performed:

1. **`Ballot.challenge_window_hours`** (new optional field, canon section
   15.1): an integer number of hours. When unset, the repository-wide
   default (72, per ADR-009 item 13) applies; when set, it overrides the
   default for that specific ballot — this is exactly the "configurable
   per ballot" requirement from the owner's amendment. Backward
   compatible: existing tooling that does not know this field simply
   does not see it; no existing field's meaning changes.
2. **`ResultPublication.challenge_deadline_at`** (new field, canon
   section 15.6): a timestamp, computed at publication time as
   `published_at + challenge_window_hours` (from the `Ballot` referenced
   by `ballot_id`, or the default if unset). This is the authoritative
   cutoff a `ResultPublication` is provisional until, per ADR-009 items
   12 and 13.

**Deliberately not proposed here, and left to a later, separate ADR if
ever needed**: a stored `finality_status`/"provisional vs final" flag on
`ResultPublication`, a canonical `IntegrityChallenge`-type entity for
submitting and adjudicating a technical challenge, and any new canonical
event marking finalization (e.g. a hypothetical `result.finalized`). None
of these is required to satisfy ADR-009 item 13's actual requirement —
"final" can be computed at read time as `now() >= challenge_deadline_at`
AND no accepted challenge exists, using only the two fields above, and
"no accepted challenge exists" is itself a query PACK-03's own
implementation can answer using its own (non-canonical) records of
submitted challenges. Proposing a full challenge-submission entity now
would be scope creep beyond what item 13 actually asked for, and is
better designed once PACK-03's own implementation clarifies what a
"technical challenge" concretely looks like in this repository (a
question ADR-009 never addressed and this ADR does not attempt to
answer either).

**Finality clarification (owner amendment, now part of this Decision):**
`challenge_deadline_at` expiring is a necessary but not sufficient
condition for a `ResultPublication` to be final. The canon text itself
(section 15.6) now states this directly, so the constraint lives in the
canon, not only in this ADR or in a future implementation's code comments:
no module may treat a `ResultPublication` as final purely because
`now() >= challenge_deadline_at`; until a canonical or explicitly
approved technical-challenge registration/adjudication mechanism exists
(its own future ADR), every `ResultPublication` remains
provisional/finality-pending at the application level, and PACK-03 must
not invent an informal, pack-local substitute for that missing mechanism.
Tests written against this behavior may assert the deadline computation
and the provisional-window logic; they must not assert or simulate an
end-to-end challenge-adjudication outcome that does not yet exist.

Option B is rejected: it would let `Ballot`/`ResultPublication`'s real,
practical shape silently diverge from what the canon says those entities
contain, which is precisely the undocumented-deviation risk canon
section 26 exists to prevent — a challenge window governing when a vote
result becomes final is exactly the kind of "политически значимое"
(politically significant, INV-04's own language) property the canon is
supposed to be the source of truth for, not a pack-local implementation
detail. Option C is rejected per the owner's explicit instruction.

## Consequences

`docs/canonical/TZ-00-domain-event-canon.md` section 15.1 now has one new
field bullet under `Ballot` (`challenge_window_hours`) plus a one-line
clarifying sentence on its default/configurability; section 15.6 now has
one new field bullet under `ResultPublication` (`challenge_deadline_at`)
plus the finality clarification paragraph from Owner decision, written
directly into the canon text. `docs/canonical/canon-version.json`'s
`canon_version` moved `0.1.0 → 0.2.0` (the first time this project has
ever bumped that value — every prior pack only bumped
`REPOSITORY_VERSION`, a separate, repository-side counter, while
`CANON_VERSION` stayed `0.1.0` throughout PACK-01 and PACK-02), mirrored
in `packages/python/epd2-core/src/epd2_core/version.py` and
`packages/typescript/epd2-types/src/version.ts`, with the two
version-consistency unit tests
(`packages/python/epd2-core/tests/test_version.py`,
`packages/typescript/epd2-types/tests/version.test.ts`) updated to match
and `scripts/verify_versions.py` re-run clean. `docs/canonical/README.md`'s
own version mention and `docs/handover/PACK-03-SPEC.md`'s canon-dependency
checksum block were updated to the new hash; `docs/handover/PACK-02-REPORT.md`'s
historical checksum citations were deliberately left unchanged, since they
correctly describe canon's state during PACK-02's own, already-closed
verification — not the current state. This was a materially different,
higher-scrutiny kind of change than anything this project had done
before and was reviewed as such, not rubber-stamped merely because
ADR-009 had already established the need for it.

## Security impact

None directly. This ADR only adds two fields that let "when is a result
final" be computed rather than assumed; it does not change who may
submit or adjudicate a challenge (out of scope, per Decision above) or
weaken any existing fail-closed behavior. If anything, it closes a gap:
without these fields, "final" would have no canonical definition at all,
which is a worse state for INV-09 (a refusal/decision must be explicable)
than having one.

## Data impact

Two new optional/derived fields on two existing canonical entities
(`Ballot`, `ResultPublication`). No existing field's meaning, type, or
owner changes. No new canonical entity, status, or event is introduced.
Fully backward compatible per canon section 25's own definition of a
minor change.

## Migration impact

None yet — no `Ballot` or `ResultPublication` exists in this repository
today, and this ADR's acceptance does not itself create any PACK-03
service code (still not implemented — see this task's own explicit
instruction). Once PACK-03 implements these entities, any `Ballot`
created before this ADR (if any, which there will not be) would simply
have `challenge_window_hours` unset and fall back to the repository-wide
default; no backfill is required for a genuinely optional field.

## Reversibility

Reversible with cost once real ballots exist and use
`challenge_window_hours`/`challenge_deadline_at` — removing the fields
afterward would be a major-version-equivalent change per canon section
25 ("изменение обязательного поля" only applies to required fields, but
removing a field consumers have come to depend on has the same practical
migration cost). Before any real ballot exists, this remains a
low-cost, purely additive change to accept or amend.

## Related canon version

Authored against canon version `0.1.0`; performs the minor-version bump
to `0.2.0` described in Consequences, now reflected in the canon document
itself. This is the specific canon change ADR-009 item 13 required. Any
future canonical challenge-registration/adjudication mechanism (Decision's
"deliberately not proposed" note) is out of scope here and requires its
own, separate ADR before it can be implemented — this ADR's acceptance
does not pre-authorize it.
