# ADR-085 — Account recovery is a governed workflow, not a support action

**Status:** proposed
**Round:** PACK-14 — Identity, Authentication & Account Security (specification and ADR only)
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

> **Architecture correction (2026-07-30).** The decision below is unchanged.
> The open questions it left are now closed; the closures are recorded in
> `docs/packs/PACK-14/PACK-14-SPECIFICATION.md` §29 and summarised per ADR
> in the note that follows.
>
> **Recovery assurance (OD-P14-10) — this replaces binding rule 1's
> absolute wording.** Recovery **may** use different evidence from the lost
> credential; that is what recovery is. What must hold is the **resulting
> confidence**: equivalent, or carrying an explicit reason-coded risk
> acceptance by a named authority. **High-assurance recovery requires dual
> control, a cooling-off period and out-of-band notification — all three.**
> **Emergency recovery restores access and cannot immediately authorize
> high-risk actions.** Old credentials and all sessions are revoked
> **before** completion.
>
> **SMS OTP (OD-P14-09)** may contribute only as a low-weight recovery
> signal, never as deciding evidence, and it grants no assurance.

## Context

Recovery is where every strong authentication system is actually broken.
The attacker does not defeat the passkey; they persuade a support agent, or
they take over the email account the reset link goes to, or they answer
questions whose answers are on a public candidate profile. In a political
organization the attacker may also be an insider with a plausible reason to
help.

## Decision

**Recovery is a governed workflow with its own evidence, and no single
actor can complete it.**

The normative sequence:

```text
recovery requested
→ risk assessed
→ alternate verification
→ cooling-off if required
→ old credentials revoked
→ sessions revoked
→ new credential enrolled
→ out-of-band notification
→ recovery completed
```

Binding rules:

1. **Recovery is not weaker than the authentication it replaces** unless a
   named authority explicitly accepts the risk, with a reason code and
   evidence. "The user could not log in" is not a risk acceptance.
2. **No support agent can unilaterally take over an account.** Separation
   of duties applies: the actor who assesses is not the actor who approves,
   and no reviewer approves their own recovery action (ADR-087).
3. **No security questions. No reliance on publicly discoverable personal
   facts.** For candidates and office-holders, date of birth and mother's
   maiden name are published campaign material.
4. A **cooling-off period** applies where risk warrants it, with
   out-of-band notification during the window, so the legitimate holder can
   stop a fraudulent recovery before it completes.
5. Completion **revokes prior credentials and sessions**. A recovery that
   leaves the attacker's session alive has recovered nothing.
6. Recovery produces **evidence** and supports **dispute**: a person who
   says "I did not request this" must have a path that produces a record.
7. Emergency recovery exists, is reason-coded, is notified out of band, and
   is reviewed after the fact — never silent.

## Consequences

Recovery is slower than a reset link. That is the decision. The threat
model records support-engineering, insider reset and malicious recovery as
first-class threats, and this is the control that answers them.

The forms layer carries the consequence into the user-facing surface: the
recovery request, the suspicious-login confirmation and the privileged
recovery approval are all governed forms with real German text, not ad-hoc
support tickets.
