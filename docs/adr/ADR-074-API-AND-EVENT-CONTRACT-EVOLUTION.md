# ADR-074 — API and event contract evolution

**Status:** accepted
**Specification round:** PACK-13 — Production Data Plane & Contract Evolution (specification and ADR only)
**Implementation round:** PACK-13 Implementation Candidate · **Repository version:** `0.13.0` · **Canon version:** unchanged at `0.8.0`

The decision below is implemented in **reference form** by
`services/data-plane-service`. Reference form means the contracts, the
governed workflows and the refusals are real and tested; the production
data plane is not deployed and is not claimed. **NOT PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.** See
`docs/handover/PACK-13-IMPLEMENTATION-CANDIDATE-REPORT.md` and
`docs/handover/PACK-13-KNOWN-LIMITATIONS.md`.

## Context

Contracts must change. The question is whether changes are classified
honestly. Automated compatibility checkers answer a narrow structural
question — did a field disappear, did a type change — and answer it well.
They cannot answer the question that actually breaks consumers: **did the
meaning change while the bytes stayed the same?**

## Decision

Five compatibility modes: backward, forward, full, breaking, and
**unknown / manual review required**.

Three decisions carry the weight:

1. **`unknown` is a first-class outcome and the default** when the checker
   cannot decide. It is never collapsed into "probably compatible". The
   dangerous change is precisely the unclassifiable one.
2. **An additive change is not automatically safe.** Adding a field changes
   meaning if absence previously carried meaning, if validation is strict,
   or if the field creates an obligation the consumer does not know about.
3. **Six change classes are structurally invisible and always require
   semantic review**: enum meaning change; reason-code semantics; event
   meaning; organization-scope semantics; identity linkage; retention
   semantics; legal effect. For every one of these, the serialized bytes
   may be identical before and after. The registry therefore stores the
   **automated verdict and the human verdict as separate fields** — an
   assessment carrying only the tool's answer is incomplete.

For APIs: endpoint identity is stable; **no field is ever reused for a new
meaning**; **reason-code meaning never changes**; no contract change
silently widens privilege; no field is removed before consumer migration is
demonstrated; version negotiation is explicit with no silently-moving
"latest".

For events: **a historical event is never rewritten** — correction is a new
event referencing the original. Upcasters are deterministic and tested over
recorded historical payloads, and **an upcaster invents no legal facts**:
where the new schema needs a fact the old event lacks, the result is an
explicit not-determined value or a refusal, never a plausible default.
**An unknown enum value never maps to a default**, because defaulting an
unknown status to "normal" is how a novel failure becomes invisible.

Governance: a breaking change records thirteen mandatory fields, and one
missing field makes it unapprovable. **A feature flag may not bypass a
compatibility or migration gate** — `FIR-INV-006` in the contract domain. A
flag may control rollout of an approved change; it may not stand in for the
approval.

## Consequences

**Positive.** Meaning changes get human attention where tools are blind.
Consumers get real deprecation windows. Reason codes stay stable for
auditors.

**Negative, and accepted.** Contract change is slower. Enum extension needs
review, which will feel disproportionate to whoever is adding one. Semantic
review depends on a competent reviewer — which is why the requirement names
the _owner_, who knows the semantics.

**Rejected.** _Trust the automated checker_ — rejected: it cannot see the
six invisible classes. _Version everything on every change_ — rejected:
version churn trains consumers to ignore versions.
