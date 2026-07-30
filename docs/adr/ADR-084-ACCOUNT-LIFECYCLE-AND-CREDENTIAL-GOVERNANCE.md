# ADR-084 — Account lifecycle and credential governance

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
> **Account lifecycle representation (OD-P14-01) — decided, and the
> decision replaces this ADR's point 1.** The canonical `AccountStatus`
> enum is **not** extended. Canon 7.2's six values stand, and `locked`,
> `closure_pending` and `deleted_or_anonymized` are **not statuses** in any
> normative list. Instead: a technical lock is an **`AccountLock` record**;
> a security quarantine is an **`AccountRestriction`** of the security
> class; closure-pending is a state of **`AccountClosureRequest`**; and
> anonymization or deletion are **lifecycle outcomes and events**, not
> active statuses. Several may hold at once — an account can be `active`
> with a lock in force and a closure request pending — and each fact stays
> separately queryable, explainable and reversible.
>
> **Ownership (OD-P14-02):** `identity-service` owns the Account Registry
> and the Credential Registry as internally separated modules. Canonical
> ownership of `Account` (canon 7.2) is unchanged.

## Context

Canon 7.2 gives `Account` six statuses: `pending`, `active`,
`restricted`, `suspended`, `recovery_pending`, `closed`. Operationally
several distinct situations are currently being pushed through those six,
and the distinctions matter legally: a technical lock after failed logins,
a security quarantine after a suspected takeover, a membership suspension
decided by a party organ, and a voluntary closure requested by the person
are four different things with four different authorities and four
different reversibility rules.

Collapsing them produces the failure everyone recognises afterwards: a
member is told they were "suspended" and cannot find out by whom, why, or
how to contest it.

## Decision

1. **Account lifecycle states are additive over canon 7.2 and never
   redefine it.** PACK-14 records `locked`, `closure_pending` and
   `deleted_or_anonymized` as additional operational states in the
   _specification_; whether they become canon values, sub-states of
   `restricted`/`closed`, or service-level state, is an open decision
   recorded rather than silently settled (OD-P14-01).
2. **Technical lock, security quarantine, membership suspension and
   voluntary closure are never the same state.** Each carries its own
   authority reference, reason code and reversal path. An account status
   never encodes a membership decision, and a membership decision never
   sets an account status directly (canon 19d.9's two-stage rule).
3. **Credential lifecycle is separate from account lifecycle.** Enrolling,
   verifying, revoking and replacing a credential are governed operations
   with their own events and evidence. Revoking every credential does not
   close the account, and closing the account does not silently leave
   credentials valid.
4. **Closure is a request with a decision**, not an immediate destructive
   act: closure requested → cooling-off where applicable → closed →
   anonymized where permitted and required. Retention obligations and
   legal holds (PACK-09) survive closure; evidence is not destroyed to
   satisfy a convenience.
5. Contact identifiers (email, phone) are **mutable attributes, never
   identifiers**. Change requires verification of the new channel and
   notification to **both** the old and the new one, because notifying only
   the new channel is precisely how a takeover goes unnoticed.
6. A recently changed contact **may not be the sole basis for recovery**.

## Consequences

More states and more events than a minimal design would carry, and a
per-state authority and reason code for each. The alternative is a system
where "your account is restricted" is unexplainable, which is not
acceptable for an organization whose members have procedural rights against
it.

Whether the additional states belong in canon is deliberately left open
rather than assumed; ADR-084 changes no canon and the canon assessment
records why the round does not need to.
