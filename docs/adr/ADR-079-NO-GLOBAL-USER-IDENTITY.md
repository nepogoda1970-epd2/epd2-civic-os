# ADR-079 — No global user identity

**Status:** proposed
**Round:** PACK-14 — Identity, Authentication & Account Security (specification and ADR only)
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

## Context

Every system that has ever needed to know "who is this person" has, sooner
or later, created one identifier that answers it everywhere. It is the
single most convenient thing an architecture can do and the single most
destructive thing this one could do. `FIR-INV-001` has forbidden it since
the register began; PACK-13 enforced its structural absence in the data
plane (`GLOBAL_IDENTITY_KEYS`, ADR-070). PACK-14 is the round where the
pressure becomes real, because PACK-14 is the round that finally has to
say who logged in.

The pressure arrives in ordinary, reasonable-sounding forms: an email
address is unique, so use it as the key; the account ID already exists, so
put it in every event; the identity provider returns a stable subject
claim, so store it beside everything; the membership number is printed on
the card, so let people log in with it. Each is locally sensible. Together
they reconstruct the global identifier by accident.

## Decision

**No identifier may exist that correlates a person across all domains, and
no existing identifier may be repurposed into one.**

Concretely:

1. `account_id` identifies a **technical account** used for
   authentication and session management. It is not a person, a member, a
   voter, a communication persona or a public number.
2. No domain outside the Account Registry receives `account_id` as its
   integration key. Domains receive a **purpose-scoped actor reference**
   derived per purpose, per organizational scope and per domain owner.
3. The following are explicitly forbidden as universal identifiers or as
   join keys between domains: email address, phone number, membership
   number, `account_id`, `person_record_id`, national ID, eID subject
   identifier, device identifier, communication persona identifier, and any
   provider-issued stable subject claim.
4. A correlation between two identifier spaces exists **only** through an
   explicit governed mapping boundary carrying purpose, organizational
   scope, domain owner, access policy, retention and audit evidence — and
   carrying an explicit prohibition on uncontrolled correlation.
5. A mapping boundary is not a table anyone may join. It is a governed
   operation with a reason code, and its absence is a refusal, never a
   default allow.

## Consequences

Some things become harder, and the specification says so rather than
pretending otherwise. Support cannot answer "show me everything about this
person" from one query, because no such query exists. Analytics cannot
count distinct humans across domains. Duplicate-account detection cannot
work by matching email and date of birth, so it becomes a reviewed,
reason-coded process instead of an automatic merge (ADR-080).

What is bought is the only thing worth buying here: **the correlation that
would make identity/ballot unlinkability rhetorical rather than structural
does not exist to be exploited, leaked or subpoenaed.** A control that
depends on nobody performing a join is not a control. A control that
depends on the join being unrepresentable is.

## Relationship to existing canon

None of this amends canon. Canon 7.2 already defines `Account` as a
_technical_ account; canon 19d.2's `IdentityRecord` is already owned by
identity verification and already forbids using verification as a proxy for
citizenship; canon 19d.8 already fixes five never-interchangeable concepts.
ADR-079 states the prohibition that those separations exist to serve.
