# Document version integrity

> `FIR-INV-010`: "Historical versions must never be rewritten. Documents
> must preserve cryptographically linked history." ADR-057.

## The rule

```text
version_hash = sha256(canonical_dumps(hashable_fields(version)) + previous_version_hash)
GENESIS_PREVIOUS_HASH = "0" * 64
```

Identical in construction to `audit-core.hash_chain.compute_event_hash`
(ADR-003). Deliberately: two chaining schemes in one repository is one too
many, and an auditor who has verified one already knows how to verify the
other.

## What the hash covers

| In                                             | Out                   |
| ---------------------------------------------- | --------------------- |
| `version_id`, `document_id`, `version_number`  | `state`               |
| organizational scope                           | `history`             |
| `kind`, `sensitivity`, `title_reference`       | `version_hash` itself |
| the complete content descriptor                |                       |
| the complete provenance                        |                       |
| `recorded_at`, `recorded_by` **in full**       |                       |
| `corrects_version_number`, `correction_reason` |                       |

`recorded_by` includes `actor_reference`, so "who recorded this" is as
protected as what was recorded — the attribution half of `FIR-INV-010`.

`state` and `history` are out for a specific reason: if `state` were hashed,
approving version 3 would change its hash and invalidate versions 4..n. The
chain would then break on perfectly legitimate acts, so routinely that a
real break would go unnoticed.

## The two attacks, and why both checks are needed

| Attack                                    | Chain check                   | Content check |
| ----------------------------------------- | ----------------------------- | ------------- |
| Rewrite a version record                  | **fails**                     | passes        |
| Remove a version                          | **fails**                     | passes        |
| Re-parent a version (graft a fork)        | **fails**                     | passes        |
| Swap the bytes behind an untouched record | passes                        | **fails**     |
| Swap the bytes _and_ the recorded digest  | **fails**                     | passes        |
| Rewrite a version and reseal it           | **fails at the next version** | passes        |

`application.verify_document_integrity` runs both, which is why it catches
every row.

## Three independent defences

1. **Detect.** `versions.verify_version_chain` recomputes every hash and
   checks every link. Returns a result rather than raising, so an operator
   sweeping a store gets every finding rather than stopping at the first.
2. **Refuse to perform.** `storage.InMemoryDocumentVersionStore.append`
   rejects a replacement, a number that is not head+1, and a
   `previous_version_hash` that is not the head's hash.
   `record_state_change` compares `hashable_fields`, not merely the stored
   hash, so a covered field cannot be altered without resealing and slipped
   past.
3. **Refuse to build on.** Every command re-verifies before acting.

## Workflow-level immutability

`returned_for_revision` is **terminal for that version**. Revising means
creating version N+1. That is what makes "historical versions are never
rewritten" true of the workflow and not only of the storage layer.

A correction is likewise a new version carrying `corrects_version_number`
and a reason code. The corrected version keeps its hash, its state and its
history.

## What this does not prove

**Tamper evidence, not tamper resistance.** An actor with write access to
the entire store could rewrite every version and recompute every hash. The
controls that would close that gap are countersigning by an external party
and anchoring the head hash somewhere this repository does not control.
Neither is in this round. `GovernedDocument.head_version_hash` exists partly
so that an external anchor has one obvious place to be recorded when a later
round adds one.

`verify_version_chain` is therefore a detection mechanism **to be run**, not
a property to be assumed. See `docs/handover/PACK-11-KNOWN-LIMITATIONS.md`.
