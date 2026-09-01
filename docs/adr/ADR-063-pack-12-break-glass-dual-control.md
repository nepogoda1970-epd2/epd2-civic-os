# ADR-063: Break-glass as a separate, dual-controlled, notified workflow

## Status

`proposed`

## Date

2026-07-29

## Context

`FIR-INV-009` requires that privileged access be "followed by out-of-band
notification for break-glass". `FIR-INV-006` requires that feature flags
never disable hard invariants, audit obligations, separation of duties or
security gates. PACK-10 stated the same rule in its own terms and made it
quotable as a module constant: `NO_BREAK_GLASS_NOTE` — "separation of
duties that a flag can disable is separation of duties that was never in
force".

PACK-10's position was that finance has **no** break-glass at all.
PACK-12 cannot take that position: privileged administration is precisely
where genuine emergencies occur. The question is therefore not whether
emergency access exists, but what shape makes it survivable.

## Problem

1. If break-glass is a parameter of the ordinary approval workflow, it
   becomes the cheapest path through it, and the ordinary workflow
   becomes decorative.
2. If break-glass is single-controlled, it is a self-service escalation.
3. If its notification can be suppressed by the person who activated it,
   the notification is theatre.
4. If it renews automatically, "temporary" becomes permanent by
   inattention.
5. If it can reach ballot content or disable audit, it becomes the
   universal bypass of every other guarantee in the platform.

## Considered options

- **Option A — no break-glass, as in PACK-10.** Cleanest, and wrong here:
  an operator locked out during a genuine incident will obtain access
  some other way, and that way will be ungoverned. Rejected.
- **Option B — break-glass as an escalation flag on the ordinary
  request.** Rejected: makes the bypass a field.
- **Option C — a separate workflow with its own object, its own event
  family, mandatory dual control, narrow scope, short hard expiry,
  mandatory unsuppressible out-of-band notification, mandatory
  independent post-hoc review, immutable justification, and explicit
  carve-outs that break-glass reaches neither ballot content nor audit
  nor any hard invariant.** **Chosen.**

## Decision

Break-glass is governed by `P12-BG-001` through `P12-BG-014`.

Three of those deserve naming here because they are the ones an
implementation is most likely to soften:

- `P12-BG-007` — the notification MUST NOT be suppressible, delayable or
  redirectable by the activator **or by any subject that actor can
  direct**. The second clause matters: an activator who is also the
  administrator of the notification channel has suppressed it without
  touching the suppression control.
- `P12-BG-008` — a break-glass whose notification could not be dispatched
  MUST be recorded as such and escalated, never silently completed. The
  event is emitted on failure too.
- `P12-BG-013` — renewal is a new dual-controlled decision. There is no
  extension.

The transport and provider for the out-of-band notification are **not**
decided here; they belong to the later gateway and incident packs. What
is fixed now is that the notification event and its evidence are
mandatory, so that the later pack inherits an obligation rather than a
blank space.

## Consequences

Easier: emergency access exists and is governed rather than improvised;
every use is visible to someone who was not involved; the post-hoc review
is a scheduled certainty, not a discretionary follow-up.

Harder: dual control during an incident is slower than acting alone, and
there will be incidents where that is genuinely costly. This ADR accepts
that cost. The mitigation is that the scope is narrow and the expiry
short, so the second approver is agreeing to something small.

## Security impact

Addresses T-P12-19 (insider use of break-glass) and T-P12-20
(break-glass without independent notification), and reinforces T-P12-21
(privileged access to voting secrets) through `P12-BG-010`.

Residual risk stated plainly: a genuine-looking emergency with a
colluding approver defeats dual control. Mandatory independent post-hoc
review is the compensating control and is the reason `P12-BG-014` is not
discretionary.

## Data impact

Introduces `BreakGlassRequest`, `BreakGlassDecision`,
`BreakGlassActivation`, `OutOfBandNotificationRecord` and
`BreakGlassIndependentReview`, owned by PACK-12.

## Migration impact

None in this round.

## Reversibility

Effectively irreversible in one direction: once an organization has
governed emergency access, removing it returns to ungoverned improvisation.
The parameters (duration, scope breadth) are tunable; the shape is not.

## Related canon version

Authored against canon `0.8.0`. Proposes no canon version bump.
