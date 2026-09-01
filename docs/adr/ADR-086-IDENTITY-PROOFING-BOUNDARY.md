# ADR-086 — Identity proofing is a bounded case, not a person database

**Status:** proposed
**Round:** PACK-14 — Identity, Authentication & Account Security (specification and ADR only)
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

## Context

Some acts require knowing that a real, specific person is behind an
account: admission to membership, candidacy, certain finance operations.
Identity proofing produces exactly that, and it produces the most sensitive
data the system will ever hold — identity documents, dates of birth,
residence and citizenship attributes, all of which canon 19d.2 already
governs and already forbids using as proxies for one another.

The failure mode is to let a proofing subsystem quietly become the person
registry everything else joins to.

## Decision

1. **Four concepts are never equivalent**, and no code path may treat one
   as evidence of another:

   ```text
   authentication      — who is operating this session, and how strongly
   identity proofing   — whether a claimed real-world identity was verified
   membership eligibility — whether the party's rules admit this person
   authorization       — whether this actor may perform this act now
   ```

   Authentication does not prove legal identity. Identity proofing does not
   approve membership (canon 19d.9's two-stage rule stands). Membership does
   not create a voting credential (ADR-088).

2. **Proofing is a case with a lifecycle**, not an attribute set: started,
   evidence received, verified, rejected, manual review required. Each
   carries method, evidence reference, assurance and decision authority.

3. Proofing levels are ordered and named — self-asserted, email-verified,
   phone-verified, document-assisted, in-person, eID, organizational
   attestation, manually reviewed — and each maps to an identity assurance
   value on canon 19d.2's existing `none`/`low`/`substantial`/`high`
   scale rather than a new one.

4. **`person_record_id` is not an integration key.** It is
   domain-controlled, purpose-limited, unavailable as a general join key,
   and **optional**: many accounts never need one, and the design must not
   create one by default.

5. Evidence uses PACK-11's governed-document and evidence mechanisms rather
   than a second store, and retention follows PACK-09.

6. External providers sit behind an **adapter boundary** (ADR-086 defines
   the boundary; no provider is selected). Minimum attribute release,
   audience restriction, issuer validation, assertion freshness, replay
   prevention and a provider-outage path are required of any adapter, and
   **no provider-issued identifier ever becomes a global user ID**.

## Consequences

Proofing evidence is expensive to hold and is therefore held narrowly, for
a stated purpose, for a stated period. Where a decision can be made from a
derived boolean rather than the underlying attribute, the derived boolean
is what crosses the boundary — the pattern ADR-027 already established for
`get_identity_participation_claims`.
