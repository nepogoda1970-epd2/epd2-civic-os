# ADR-089 — Eligibility and credential issuance are separate authorities with separate stores, and neither may hold the other's reference

**Status:** proposed
**Round:** PACK-15 — Voting Trust Boundary, Eligibility & Credential Separation (specification and ADR only)
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

> **Architecture correction (2026-07-31).** The decision below is unchanged
> and is not reversed. The open questions it left are now closed; the
> closures are recorded in `docs/packs/PACK-15/PACK-15-SPECIFICATION.md`
> §32 and summarised for this ADR in the note that follows. The
> authoritative register is now
> `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`, carried at
> the canonical path, which preserves every prior entry and adds
> `FIR-OSS-001` … `FIR-OSS-006`.
>
> **The Assertion Issuer's boundary is fixed (`OD-P15-01`).** It is a
> **separately bounded module with its own storage boundary** inside the
> voting-trust service (`eligibility-service`), holding **separate signing
> keys and separate service credentials**, **structurally unable** to read
> ordinary account, person-record or membership stores, consuming **only
> minimized eligibility decisions**, and designed so that it can later
> become a **separate deployable without a contract change**. The
> separation this ADR turns on — assertion issuer versus credential issuer
> — remains a **service** boundary and is not negotiable.

## Context

`FIR-INV-004` requires that eligibility authority and credential issuance
authority be separated. It has been `approved` since the register was
written and untouched by fourteen packs, because none of them needed
either concept. PACK-15 needs both, and the moment both exist the
separation stops being a principle and becomes an implementation question
with a wrong answer available at every step.

The wrong answer is always the same shape: one service that decides who may
vote and then hands that person their means of voting. It is the obvious
design. It is what almost every internal voting tool does. It produces a
system in which one component, one database and one operator know both who
was entitled and what they were given — and from there, everything
downstream is attributable in principle, whatever the ballot format
promises.

Canon already anticipated this. `eligibility-service` owns
`EligibilityRule`, `EligibilityDecision` and `EligibilitySnapshot` (canon 9,
19d.4). `credential-service` owns `ParticipationCredential` (canon 10.1)
with a structural prohibition on identity fields. They are different
services with different owners, and canon forbids `eligibility-service`
any read or write edge to `voting-service`, `tally-service` or
`VoteEnvelope`. The separation exists on paper. PACK-15 has to make it
survive an implementation that needs the two to cooperate.

## Decision

**Eligibility determination and credential issuance are two authorities,
in two bounded contexts, owned by two services, with two stores, two keys
and two audit streams. Neither holds a reference to the other's artifact.**

1. **Eligibility is decided on the identity side**, by
   `eligibility-service`, against a frozen rule-set version, with reason
   codes, evidence references and a validity window. It knows which
   participant it is deciding about. That is correct and is where
   identification stops.

2. **Credentials are issued on the voting side**, by
   `credential-service`, against a verified minimized assertion. It knows
   the context, the class and the nonce. It does not know, and has no
   means of learning, which participant is in front of it.

3. **The Eligibility Service holds no credential reference.** Not in a
   case, not in a decision, not in an event, not in a log, not in a
   report.

4. **The Credential Issuer holds no eligibility reference.** It records the
   assertion's nonce as _spent_ — set membership, not a mapping — and
   records the credential separately with no back-reference. ADR-093 is
   the decision record for that construction.

5. **Duplicate prevention is split across the two sides**: one assertion
   per participation unit, enforced where the participant is known; one
   credential per assertion nonce, enforced where the nonce is known.
   Between them the effect is exactly-once, and neither side needs the
   other's identifier to achieve it.

6. **No role, grant, service account, flag or emergency path may hold both
   authorities** in the same voting context (`SD-06`). This binds machine
   principals as strictly as people, because a backup job with read access
   to both stores is an election role that nobody named.

## Consequences

Some things become harder, and the round accepts them rather than
engineering around them.

**Support becomes harder.** "This member says they did not receive their
access" cannot be resolved by looking up the member's credential, because
no such lookup exists. It is resolved through the holder-supplied
reference, the governed reissue path, and — where those fail — an honest
statement that the participation is lost for that context. This is a real
cost, paid deliberately.

**Reconciliation becomes harder.** Counting assertions issued and
credentials minted and finding a discrepancy is possible; finding _which_
one is missing is not. The auditor's evidence bundles are designed around
counts for exactly this reason (ADR-097).

**A second mechanism is not created.** Break-glass, dual control and
privileged access reuse PACK-12 unchanged. The only addition is the rule
that no grant may span the two sides.

**What is gained** is that a compromise of either service, a subpoena
served on either store, an insider in either role, or a misconfigured
replica of either database yields half a chain and no more. That property
is the reason `FIR-INV-004` exists, and it is only real if it is
structural.

## Alternatives rejected

**One service, two modules, strong access control.** Rejected: access
control fails, and a join that is merely forbidden is still available to
anyone who reaches the database. The invariant has to hold against the
operator, not only against the application.

**One service, with the linkage encrypted.** Rejected: the ciphertext and
the key are both inside the same trust boundary, so this is access control
with extra steps, and it produces a system that _can_ be made to answer the
question — which is the property being refused.

**Separation by policy, with the pairing stored "for audit".** Rejected:
this is the failure mode the round exists to prevent. The audit's need is
met by counts and per-stream integrity (ADR-097), not by the pair.
