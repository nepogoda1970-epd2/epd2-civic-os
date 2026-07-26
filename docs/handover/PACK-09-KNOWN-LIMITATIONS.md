# PACK-09 — known limitations

Repository version `0.9.0`, canon `0.7.0`. Authoritative scope document
for this pack from the CANDIDATE-2 round onward: **EPD² Architecture &
Domain Framework 0.8.1** (Roadmap Amendment).

This file records what PACK-09 does **not** do, and — where a guarantee
is partial — exactly where its edge is. It is deliberately separate from
the implementation report: a limitation that only appears in a report
gets read once.

None of the items below are defects. Each is either a scope boundary
assigned to a later pack, or a place where an honest partial guarantee is
better than an overclaimed complete one.

---

## 1. This is not a production system

No production persistence (every store is in-memory; PACK-13), no HTTP
server, no event-bus publication, no deployment artefacts, no schema
registry. `contracts/openapi/pack-09.yaml` documents a transport-neutral
contract exercised through the application-layer functions directly, not
over HTTP.

**No claim of legal compliance is made.** The pack implements governed
workflows, evidence references, reason-coded refusals and auditability.
Whether a given retention period, deemed-service rule, notice method or
processing basis satisfies the GDPR, the BDSG or the Parteiengesetz is a
legal determination made by humans outside this system. The code refuses
to _presume_ those answers; it does not supply them.

---

## 2. Legal Hold propagation is only as complete as what is registered

`assert_hold_propagation_resolved` refuses destruction while any known
derivative of a hold — replica, search index, export dataset, backup set,
cached rendition — is in state `unknown`, `pending` or `failed`.

**An empty propagation set is treated as resolved.** This asymmetry is
deliberate: PACK-09 can only reason about derivatives it has been told
about. It refuses on the ones it has; it cannot refuse on ones nobody
registered.

The consequence, stated plainly: **propagation completeness is a
deployment responsibility, not a guarantee this service makes.** A
deployment that creates a search index over held records and never calls
`register_hold_propagation` will see destruction authorized while that
index still holds the data. Nothing in this repository can detect that,
because nothing in this repository knows the index exists.

`assert_destruction_propagation_resolved` is a _separate_ assertion, not a
required argument on `authorize_destruction`. A caller that participates
in propagation must invoke it; one that does not, does not.

---

## 3. Legal effect requires a human step that nothing performs automatically

Only `NoticeEffectDecision` can start a procedural deadline (ADR-043). It
is produced by `determine_service_effect`, which a competent authority
must actually call.

A deployment that issues notices and records service attempts but never
determines effect will find that **no deadline ever starts**. That is the
intended failure direction — fail-closed on a question about whether
somebody was lawfully notified — but it is a real operational obligation
and it will not announce itself.

`NoticeEffectOutcome.UNDETERMINED` is likewise a real state with no
automatic resolution. When every attempt's telemetry is unknown, the
service refuses to determine, and the matter waits for a human.

---

## 4. Deemed-service rules are structural, not jurisdictional

`DeemedServiceRule` names five presumption shapes and
`notices._supports` decides which telemetry can support each. What it
encodes is the _structure_ of a presumption — reconciled evidence of a
particular kind is required for a particular rule — not any specific
jurisdiction's law.

`rule_reference` on every `NoticeEffectDecision` is where the actual
legal basis is recorded, as an opaque reference. PACK-09 does not
validate it, does not know what it points at, and takes no position on
whether the rule invoked is the right one for the matter.

One case is deliberately unresolved: `DeliveryTelemetryStatus.REFUSED` is
**not** classified as a delivery failure, because refusing service
constitutes service in several jurisdictions. But no rule currently
accepts it on its own either, so a refused delivery falls to
`SERVICE_NOT_PROVEN` until an authority selects a rule that covers
refusal. Fail-closed on a genuinely contested legal question was
preferred to silently picking either answer.

---

## 5. Party handles are unlinkable by construction, which cuts both ways

`mint_case_party_reference` produces a random per-case UUID with no
derivation from anything and no resolution path. Two cases involving the
same real person carry two unrelated handles.

The cost is real and permanent: **PACK-09 cannot answer "all cases
involving this person"**, and no later pack can make it able to without
introducing exactly the global identifier Framework hard invariant 1
forbids. A deployment that needs cross-case linkage needs a governance
decision and an ADR, not a query.

---

## 6. Placeholder references point at packs that do not exist yet

`references.py` publishes `EvidenceRef`, `DocumentRef`, `MinutesRef`,
`FinanceEvidenceRef`, `NoticeProofPackageRef` and `AdmissionDecisionRef`
as _forward declarations_. PACK-09 records that a filing cites evidence,
that a hearing produced minutes, that a service attempt has a proof
package — never their content, and never any assertion about them.

In particular: PACK-09 makes **no claim** that a referenced document is
authentic, that referenced evidence was admitted, or that a proof package
is evidence-grade. Framework hard invariants 43 and 44 assign all of that
to PACK-11. A `NoticeEffectDecision` carrying a
`proof_package_reference` asserts that the deciding authority said one
exists, and nothing more.

---

## 7. Scope isolation is flat, and the not-found error is intentionally uninformative

There is no hierarchy-derived inheritance anywhere: a Bund-level
organization holds nothing over a Landesverband's records without a
`CrossScopeAuthorityGrant` issued by that Landesverband and _presented_
by the caller for that operation.

A resource in another organization returns the same
`VALIDATION_RECORD_NOT_FOUND` as a resource that does not exist. That is
required (a foreign id must not disclose existence) and it is unhelpful
during debugging — a caller genuinely missing a grant sees "not found"
rather than "you need authority here". The specific
`CROSS_SCOPE_ACCESS_DENIED` / `CROSS_SCOPE_AUTHORITY_INVALID` codes are
reachable only by a caller that already asserted it holds authority
there.

---

## 8. Out of scope by assignment

Implemented nowhere in this pack, and not stubbed:

| Assigned to | Not implemented here                                                               |
| ----------- | ---------------------------------------------------------------------------------- |
| PACK-10     | Party finance accounting, Rechenschaftsbericht, sponsorship and lobbying registry  |
| PACK-11     | Document storage, evidence content, document version chains, evidence admission    |
| PACK-12     | Privileged JIT/break-glass administration, DLP                                     |
| PACK-13     | Production database, event bus, schema registry                                    |
| PACK-14     | Real IAM/eID, credential issuance                                                  |
| PACK-15/16  | Voting threat model, cryptographic voting                                          |
| PACK-17     | Production incident response                                                       |
| PACK-18     | User-facing applications                                                           |
| PACK-19     | Candidacy, nomination, ballot admission — `AdmissionDecisionRef` is interface-only |
| PACK-21     | Assemblies, motions, minutes as a domain                                           |
| PACK-22     | Communication channels, templates, message delivery                                |
| PACK-23/24  | Complaints intake, investigations                                                  |

For each of these PACK-09 publishes **only** a typed reference or a
domain-neutral primitive. No candidacy entity, no channel entity, no
finance entity and no document entity exists in this service.

---

## 9. Verification limitations of the CANDIDATE-2 round

The environment this round was produced in has no network egress to
`pypi.org`, `files.pythonhosted.org` or `registry.npmjs.org`. The
consequences are recorded precisely in `LOCAL_VERIFICATION.md` and in
section C of `docs/handover/PACK-09-IMPLEMENTATION-REPORT.md`:

- `uv sync --all-groups --frozen` was **not** run.
- `npm ci`, `npm run lint` and `npm run build` were **not** run.
- Python checks ran against a locally-assembled interpreter and tool set,
  not against the versions `uv.lock` pins.

The archive is therefore named `CANDIDATE-2`, not `PASS`. Whether the
frozen dependency set behaves identically is unverified and must be
established by a CI run.
