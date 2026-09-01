# ADR-087 — Privileged identity administration reuses PACK-12, and adds no console

**Status:** proposed
**Round:** PACK-14 — Identity, Authentication & Account Security (specification and ADR only)
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

## Context

Identity administration is the most attractive privilege in the system. An
actor who can reset credentials can become anyone; an actor who can read
proofing evidence can see everything the organization was careful not to
collect twice.

PACK-12 already built the control surface for exactly this: purpose-scoped
just-in-time grants with no unbounded window and no `renew`, dual-control
break-glass with an out-of-band notification obligation, separation of
duties re-checked at the moment of the act, and reason-coded refusals with
no free text.

## Decision

**PACK-14 defines no new privileged-administration mechanism. It defines
roles and separations that PACK-12's mechanism carries.**

Roles, each an operational assignment rather than an institutional office:

| Role                       | May                                                             | May **not**                                                     |
| -------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------- |
| Support Agent              | See account status, initiate a recovery case, notify the holder | Change credentials, complete a recovery, read proofing evidence |
| Recovery Reviewer          | Assess and decide a recovery case                               | Decide a case they initiated or are the subject of              |
| Identity Proofing Reviewer | Decide a proofing case, read the evidence for that case         | Read evidence outside the case; change account credentials      |
| Security Admin             | Restrict, quarantine and revoke sessions on security grounds    | Make a domain decision — membership, candidacy, finance         |
| System Admin               | Operate the platform                                            | Read identity content or complete an identity operation         |
| Auditor                    | Read governed evidence for oversight                            | Change anything                                                 |

Binding separations:

1. **Support is not ownership.** No support role can silently change the
   owner of an account or complete a recovery alone.
2. **No self-approval.** A reviewer never approves their own action.
3. **System Admin does not get identity content by virtue of operating the
   platform.** Infrastructure access is not domain authority — the same
   rule PACK-13 applied to the data plane.
4. **Security Admin does not get domain decision authority.** Quarantining
   an account is not deciding a membership.
5. Break-glass is reason-coded, dual-controlled, notified out of band, and
   reviewed independently afterwards. There is no standing superuser and no
   universal identity console (`FIR-INV-014`).
6. Every privileged identity action produces audit evidence before the
   corresponding event is emitted, following PACK-12's audit-before-event
   ordering.

## Consequences

Some legitimate support interactions require two people. That is the cost
of making account takeover by insider or by social engineering structurally
hard, and the threat model names both as first-class threats.

No arbitrary identity console exists to be built later "for operations."
Where an administrative surface is needed, it is a named, scoped, governed
operation with a form and a receipt — the pattern the forms layer requires.
