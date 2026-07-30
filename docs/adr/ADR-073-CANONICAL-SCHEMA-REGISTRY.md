# ADR-073 — Canonical schema registry

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

The system already carries JSON Schemas, OpenAPI descriptions, event
payload contracts and SQL migrations across twelve packs. Nothing records
which version of which artifact is active, who owns it, what it is
compatible with, or who consumes it. Contract changes are therefore
reviewed by whoever notices them.

## Decision

A **canonical schema registry** records, for every schema version:
`schema_version_id`, family, version, owner, format, `content_digest`,
`publication_decision_id`, compatibility mode, classification,
`effective_at`, `deprecated_at`, `supersession_reference`, documentation,
**example fixtures**, validation result, dependent consumers, approval
evidence, and `governance_justification` where identical content is
published as a new governed version.

Lifecycle: `draft → under_review → approved → active → deprecated →
retired`, with `rejected` and `superseded`. Every transition is a governed
act with an actor, a reason code and an event.

**Content digest and version identity are separate fields answering
separate questions.** _Content that is identical after the registry's
format-specific canonicalization produces the same content digest. Digest
equality does not itself define schema-version identity._

An earlier draft of this decision said that two byte-different but
semantically identical documents must not produce two schema versions. That
was wrong in two ways, and the correction is the substance of this
paragraph. First, it made the registry claim a **semantic equivalence
proof** it cannot perform: canonicalization removes only enumerated
serialization differences per format, and nothing more. Second, it
conflated a content fact with a **governance** fact — there are legitimate
reasons to publish identical content as a new governed version (a changed
compatibility mode, a new effective date, a corrected ownership
assignment, a republication after a governance defect), and a registry that
silently deduplicated them would erase the decision that motivated the
re-issue.

So: accidental republication of identical content is **blocked or sent to
reason-coded review**, never silently accepted and never silently merged;
identical content may be bound to a new version only with an explicit
`governance_justification`; and **historical version identity is never
rewritten because of digest equality**.

Four further decisions deserve their reasoning recorded:

1. **The registry is not a second canon** (`P13-REG-002`). It records
   artifacts and their evolution; the canon records meaning. Where they
   disagree, **the canon governs** and the disagreement is a defect. A
   registry able to override the canon would create a second normative
   authority — which is a governance failure, not an architecture choice.
2. **Retired and superseded versions are retained, never deleted.** A
   historical event validated against a retired schema must remain
   interpretable; deleting the schema orphans the history.
3. **Example fixtures are mandatory and are validated at publication.** A
   schema whose own examples do not validate is wrong, and this catches it
   before consumers do.
4. **Every schema has exactly one owner, and the owner is a domain**, not a
   platform team. A platform team can maintain a file; only the domain
   knows what a change means.

Consumer registration is how the registry knows who breaks. An unregistered
consumer receives no compatibility protection — and that consequence is
**stated to consumers**, not discovered by them.

## Consequences

**Positive.** Compatibility becomes assessable rather than guessed.
Deprecation windows become enforceable. The blast radius of a change is
knowable before it ships.

**Negative, and accepted.** Republishing identical content requires a
written justification, which will occasionally feel like ceremony over a
no-op change. Every contract change acquires registry overhead. The registry becomes a dependency of the publication path — so
its unavailability blocks publication (deliberately) while leaving existing
traffic alone. Fixtures must be maintained.

**Rejected.** _Schemas in version control only_ — rejected: git records
what changed, never who consumes it or whether they are ready.
_A vendor schema registry as the source of truth_ — rejected: it would
own governance data, and its compatibility model is not this system's.
