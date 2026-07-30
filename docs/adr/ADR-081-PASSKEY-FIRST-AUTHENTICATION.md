# ADR-081 — Passkey-first authentication

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
> **Attestation (OD-P14-08):** no universal attestation requirement; a
> **synced passkey reaches at most `substantial`**; `high` requires a
> device-bound credential or a separately approved equivalent; hardware
> attestation is required only for specifically governed privileged action
> classes; and no ordinary member is excluded for lack of attestation.
>
> **Password fallback (OD-P14-03):** the reference implementation **does**
> support controlled password fallback. Passkeys remain preferred; no new
> password-only account may be created; password login always requires MFA
> and never authorizes a consequential action alone; it caps at
> `substantial`; it can be disabled through governed configuration; and
> security questions remain prohibited. This does not weaken the
> passkey-first direction — it removes the assumption that everyone owns a
> passkey-capable device.
>
> **SMS OTP (OD-P14-09):** not a login method, not a step-up factor, and it
> carries no assurance level. It verifies a phone channel and contributes a
> low-weight recovery signal only, and the system operates with no SMS
> provider.

## Context

The dominant attack against a political organization's accounts is not
cryptographic. It is phishing, and its close relatives: credential
stuffing, password spraying, OTP relay. Any authentication design whose
strongest common path is "a secret the user can be persuaded to type into
a page" has already lost to a well-made lookalike domain, and no amount of
user education changes that.

WebAuthn/passkey authentication is origin-bound: the authenticator will not
produce an assertion for the wrong origin, which makes the entire class
structurally unavailable rather than merely discouraged.

## Decision

**Passkeys (WebAuthn) are the reference direction and the preferred method
for every account.** Other methods exist as controlled alternatives, each
carrying an explicit assurance class rather than being treated as
equivalent.

Normative points:

1. An account may hold **multiple passkeys**; a single authenticator is a
   single point of failure and the model must not encourage it.
2. Each credential records a user-supplied nickname, creation time,
   last-used time, authenticator metadata, backup eligibility and
   device-bound-versus-synced character.
3. **A synced passkey is not automatically equivalent to a device-bound
   hardware credential.** The two are recorded distinctly and may map to
   different assurance classes; treating a credential synced through a
   consumer cloud account as hardware-grade would silently make that cloud
   account the real authenticator.
4. **Attestation is not universally required.** Requiring it everywhere
   excludes ordinary users and platform authenticators for a benefit only
   some actions need. Where attestation is required, it is required by a
   named, documented risk assessment for a named action class.
5. Removing the last remaining credential is a consequential action: it
   requires step-up, notification, and a recovery path that already exists
   before removal completes.
6. Losing a device and compromising a device are different events with
   different responses; both are specified, and neither silently downgrades
   the account's assurance.

No production authenticator vendor, platform or provider is selected by
this round.

## Consequences

Registration and recovery become the hard parts of the design rather than
login, which is the correct place for the difficulty. A passkey-first
system with a weak recovery path is a password system wearing a costume —
which is why ADR-085 treats recovery as a first-class governed workflow and
not as a support convenience.

Some users will have no passkey-capable device. The alternatives in the
authentication method matrix exist for them, with honest assurance classes
and honestly restricted allowed actions, and the inclusion obligations in
`FIR-INCLUSION-001` apply.
