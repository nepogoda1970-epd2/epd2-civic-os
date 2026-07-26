# ADR-043: Official notice, service telemetry and legal effect as three separate objects

## Status

`accepted`

## Date

2026-07-26

## Context

The Architecture & Domain Framework 0.8.1 (Roadmap Amendment, authoritative
for PACK-09's scope from this round onward) states four hard invariants
that bear on one mechanism:

- **#39** — delivery and read telemetry are not legally effective notice.
- **#40** — legally effective notice requires an authorized object, a
  valid method, proof, and a governed effect decision.
- **#57** — a provider's status is not an internal legal effect without
  validation and reconciliation.
- **#59** — retry and replay do not repeat a consequential legal effect.
- **#60** — an outage does not silently change a legal deadline.

PACK-09 round 1 already implemented procedural deadlines: a
`ProceduralDeadline` whose status and `due_at` are derived from an
append-only history, with `start` / `suspend` / `resume` / `extend` /
`complete` / `escalate` / `expire` transitions, each reason-coded and
audited. What round 1 did **not** model is the question of _what is
allowed to start one_.

That gap is not cosmetic. In every system where a deadline runs from
"notification", the notification is delivered by some channel — post,
portal, e-mail — and that channel reports a status. The natural
implementation reads that status and starts the clock. That
implementation is wrong in a way that is invisible until it matters: a
mail provider's `delivered` is a statement about a transport, made by a
party with no legal standing, on evidence nobody has examined. Treating it
as service of process means an appeal window can open, run and close
because a webhook fired.

PACK-22 (communications) is a later pack and will own the channels. If
PACK-09 leaves the boundary undefined, PACK-22 will define it — and the
only shape available to a channel service is the telemetry it has.

## Problem

Where does legal effect come from, and what object owns it?

Three sub-questions, which have to be answered together:

- Is "a notice exists", "a notice was sent" and "a notice took effect"
  one object with a status field, or several objects?
- What evidence is sufficient, and who decides sufficiency?
- What stops a retry, a replay or a second webhook from producing legal
  effect twice?

## Considered options

- **Option A — a single `Notice` aggregate with a status field**
  (`issued` → `dispatched` → `delivered` → `effective`). One object, one
  lifecycle, one store. The channel updates the status; when it reaches
  `effective`, deadlines start.
- **Option B — a `Notice` plus a `service_status` value object**, where
  legal effect is a derived property computed from the telemetry and a
  configured deemed-service rule.
- **Option C — three distinct objects** — `OfficialNotice` (the
  authorized object), `ServiceAttempt` (telemetry), `NoticeEffectDecision`
  (a governed determination) — with legal effect expressible only on the
  third, and a fourth object, `DeadlineTrigger`, recording which governed
  source started which deadline exactly once.

## Decision

**Option C.**

`services/compliance-service/src/epd2_compliance_service/notices.py`
implements three types with deliberately asymmetric capabilities:

| Object                 | What it asserts                                    | Can start a deadline |
| ---------------------- | -------------------------------------------------- | -------------------- |
| `OfficialNotice`       | an authorized notice object exists for this case   | no                   |
| `ServiceAttempt`       | one attempt was made; the provider reported X      | no                   |
| `NoticeEffectDecision` | a competent authority determined the legal outcome | yes, and only it     |

Four design choices carry the invariants:

1. **`OfficialNotice` has no effect vocabulary at all.** No
   `served_at`, no `effective_at`, no `establishes_legal_effect`. The
   concept is absent from the layer, not merely false in it.

2. **The telemetry enums are named `DeliveryTelemetryStatus` and
   `ReadTelemetryStatus`.** A reviewer reading
   `attempt.delivery_status: DeliveryTelemetryStatus` is told by the type
   name what kind of claim this is. Naming is not a guard, but it is the
   cheapest one available and it survives refactoring.

3. **`ServiceAttempt.is_reconciled` gates every deemed-service rule
   without exception.** `notices._supports` requires it for all five
   rules. An unreconciled `delivered` supports nothing, which is
   invariant #57 in executable form: the difference between a provider's
   claim and evidence is a reconciliation step somebody performed against
   a proof package.

4. **`TriggerSource` contains `DELIVERY_TELEMETRY` and `READ_TELEMETRY`
   as members that are then excluded from `GOVERNED_TRIGGER_SOURCES`.**
   This is the least obvious choice in the ADR and the most deliberate.
   Omitting them entirely would make the prohibition an absence — and an
   absence cannot be tested, cited in a review, or noticed when somebody
   adds a member later. Naming them makes the refusal an assertion:
   `test_telemetry_can_never_be_a_governed_deadline_trigger` names both
   members, and `DeadlineTrigger.__post_init__` refuses both by name.

`DeadlineTrigger` is written through a create-once store keyed by
`deadline_id`, and `assert_no_duplicate_legal_effect` refuses a second
trigger from the same `NoticeEffectDecision`. Together with `event_id`
idempotency at the command layer, that is invariant #59: a retry returns
the recorded trigger; a genuinely new attempt is refused; neither
produces a second consequential effect.

Invariant #60 is handled by keeping outages **out of this mechanism
entirely**. There is no "outage" trigger source and no automatic
adjustment. A deadline whose infrastructure was unavailable is suspended
and resumed through the round-1 governed transitions, each with its own
reason code and its own audit entry, and the append-only history keeps
both. An outage therefore cannot change a deadline without somebody
having recorded that it did.

Option A was rejected because a status field is exactly the mechanism
that lets a channel write legal effect: whoever can call the status
setter can produce it, and the guard would live in whichever caller
happened to be written last. Option B was rejected for a subtler reason —
a derived property makes legal effect a _function of telemetry_, which is
invariant #39 inverted. Even with a strict rule table, the object graph
would say that enough telemetry is sufficient, and the next person to
relax the table would be relaxing a configuration value rather than
overriding a governance decision.

## Consequences

Easier: the boundary is auditable in one file. A reviewer asking "what
can start a deadline in this system?" reads `GOVERNED_TRIGGER_SOURCES`
and `determine_notice_effect`, and is done. PACK-22 gets a typed
`NoticeEffectRef` it can consume and cannot produce.

Harder: three objects where one would have been simpler, and a
determination step somebody has to actually perform. A deployment that
never calls `determine_service_effect` will find that no deadline ever
starts — which is the intended failure direction, but it is a real
operational obligation, and it is recorded in
`docs/handover/PACK-09-KNOWN-LIMITATIONS.md` rather than left to be discovered.

Also harder: `NoticeEffectOutcome.UNDETERMINED` is a real state with no
automatic resolution. When every attempt's telemetry is unknown, the
service refuses to determine and the matter waits for a human. That is
fail-closed, and it is the correct default for a question about whether
somebody was lawfully notified, but it is not a state that clears itself.

## Security impact

Positive and specific. The failure this ADR prevents is an
_availability-shaped_ attack on due process: an actor who can influence a
delivery provider's reporting — or simply a provider with an optimistic
webhook — can, under Option A or B, cause a legal deadline to run against
a party who never received anything. Under Option C that actor can at
most produce a `ServiceAttempt` whose `is_reconciled` is false, which
supports no rule.

The wire payloads carry the prohibition too: `official_notice.issued` and
`service_attempt.recorded` each publish `establishes_legal_effect: false`
as a literal field, so a subscriber that wires the wrong event to a
deadline has to override an explicit denial rather than merely omit a
check. `events.NON_LEGAL_EFFECT_NOTICE_EVENT_TYPES` names the two by
name.

No new identity surface: a notice's recipient is a per-case party handle
(`casework.mint_case_party_reference`), the proof package is a reference
to material PACK-11 will own, and no wire payload carries either.

## Data impact

Adds four entity schemas (`official-notice`, `service-attempt`,
`notice-effect-decision`, `deadline-trigger`) and four event payload
schemas. No existing entity changes shape. `ProceduralDeadline` is
untouched: the trigger is a separate record pointing at it, which is what
allows this mechanism to be added without reopening round 1's deadline
model.

## Migration impact

None. No stored shape changes and no deployed data exists.

## Why this needs its own ADR

PACK-09's brief permits at most one new ADR, and only for a genuine
architectural fork. ADR-038 through ADR-042 do not cover this one:

- **ADR-038** decides the service boundary and the dependency rule. It
  says nothing about what may start a deadline.
- **ADR-039** decides retention and Legal Hold. Different subject.
- **ADR-040** decides the processing registry. Different subject.
- **ADR-041** decides that deadlines are derived from an append-only
  history rather than stored — the closest neighbour, and the reason this
  ADR does not need to revisit deadline *representation*. But ADR-041
  answers "how is a deadline's state computed?"; it does not answer "what
  is permitted to be its origin", and the two have different failure
  modes: ADR-041 prevents an inconsistent deadline, ADR-043 prevents a
  legitimate-looking deadline that should never have started.
- **ADR-042** decides arbitration independence — who may decide. This ADR
  decides what evidence a decision may rest on.

The fork is real and was decided against two other viable options (A and
B above), both of which would have been less code. Recording it as a
consequence of an existing ADR would leave the rejected options
unrecorded, and the next person to propose Option B would have no record
of why it was refused.

## Related canon version

Authored against canon `0.7.0`. **No canon bump is proposed.** The three
new objects are compliance-side control metadata owned by one service,
and the four new events use canon section 21's envelope unchanged.
`CANON_VERSION` stays `0.7.0` and no canon-owned file is touched.
