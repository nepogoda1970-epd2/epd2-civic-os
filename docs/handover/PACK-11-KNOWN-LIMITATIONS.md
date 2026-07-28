# PACK-11 — known limitations

Named gaps, not footnotes. Each is a thing this round could have been read
as providing and does not.

## 1. The version chain is tamper _evidence_, not tamper _resistance_

`FIR-INV-010` asks for cryptographically linked history, and this round
provides it: any alteration or removal of a version in a retained sequence
makes `verify_version_chain` fail.

**What it does not prevent.** An actor with write access to the entire
store can rewrite every version and recompute every hash. The chain is
self-contained, so nothing outside the store contradicts a wholly rewritten
one.

**What would close it:** anchoring `head_version_hash` outside this
repository, or countersigning by a party that is not the store operator.
Neither is in this round — see OD-20. `verify_version_chain` is therefore a
detection mechanism _to be run_, not a property to be assumed, and an
operator who never runs it gets no benefit from it.

## 2. No production persistence

Every adapter in `storage.py` is in-memory: not concurrency-safe, not
durable, holding live object references rather than serialised rows. The
`ContentStore` holds bytes in a dict. PACK-13 owns the durable data plane.

## 3. Nothing is verified about content as a _file_

This service hashes bytes and compares digests. It does not parse, sniff,
validate or scan them. `media_type` records what a submitter declared, not
what this service confirmed. A weaponised PDF stored here is stored
faithfully.

## 4. No signature verification

`SignatureDetermination` records a determination an authority made. This
service performs no cryptographic verification, resolves no certificate
chain and knows no trust anchor. `SIGNED_UNVERIFIED` exists precisely
because the honest answer for material this platform cannot validate is
neither "signed" nor "not signed". PACK-14 owns keys and external trust
providers.

## 5. No legal or admissibility judgement

`AdmissibilityDetermination` records what a legal reviewer decided. If that
decision is wrong, this service records it faithfully. Nothing here
establishes that a stored document is a legally valid original, an
admissible exhibit, a compliant publication or conformant with the
Parteiengesetz, the Grundgesetz or any party statute.

## 6. The legal-hold picture is only as fresh as the last observation

`LegalHoldBinding` records PACK-09's answer with the moment it was
observed. This service deliberately does not cache the state across acts —
the application layer is expected to re-read before every
destruction-relevant act — but it also cannot _force_ a caller to have done
so. A caller that records a stale observation and immediately acts on it
gets a stale answer. The `indeterminate` state and its fail-closed refusal
are the mitigation, not a guarantee.

## 7. Disposition destroys nothing

`authorize_disposition` records the PACK-09 authorization and closes the
document. Executing a disposal against an in-memory reference store would
be a durability claim this round has no basis for, so it does not. What a
completed disposition should leave behind is OD-25.

## 8. No HTTP surface, no OpenAPI contract, no frontend

Deliberate, and the same choice PACK-10 made. An OpenAPI file describing
nothing runnable would make the contract suite assert against a fiction.

## 9. Renditions are supplied, not generated

`issue_publication_rendition` takes rendition bytes from the caller and
does not verify that they faithfully represent the source version. See
OD-23.

## 10. Event-stream metadata is visible to stream consumers

Event _types_ and organizational scope travel on every event. A consumer
able to read the stream learns that, for example, a legal opinion exists in
an organization — though not what it says, whom it concerns, or its title.
The publicly-projectable allow-list is four event types precisely to limit
this, but it limits the _public_ surface, not the internal stream. PACK-12
owns controlled search and export.

## 11. One person can still hold several roles

The incompatibility matrix forbids the pairs that would collapse the
three-eyes structure. It deliberately permits `document_custodian` +
`document_approver` and `document_approver` + `publication_officer`,
because forbidding them would make ordinary record-keeping in a small
organization impossible. Per-act separation covers the resulting risk —
one actor cannot perform two separated acts — but a two-person organization
determined to route around it by using two accounts is outside what this
service can detect. That is an identity problem (PACK-14), not a document
problem.

## 12. Verification in this round was not run under the real toolchain

`pytest`, `ruff`, `mypy`, `uv` and `npm` could not run in the build
sandbox (no package-index access). The 358 tests were executed with a local
runner over the same test modules; lint was approximated. `make verify` on
a networked runner is required before this candidate is considered for
PASS.
