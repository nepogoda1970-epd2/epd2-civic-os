# PACK-16D — Canon Assessment

**Round:** PACK-16D — Network-Enabled Finalization: Lockfile Regeneration,
Immutable ElectionGuard Provenance and Final Acceptance Alignment. A correction
of the PACK-16D reference-implementation candidate, not a new round.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. Conclusion

```text
NO CANON CHANGE REQUIRED
```

The precise statement of what happened to Canon, used verbatim wherever
this topic arises in this repository:

```text
CANON_VERSION remains 0.8.0.

No Canon domain, aggregate, event or invariant semantics changed.

Canon compatibility metadata continues to support
repository version 0.16.x.
```

**The third line reads "continues to support" rather than "was updated to
include", because in this round nothing was updated.** The widening happened
in the 0.16.0 round and still holds; saying "was updated" would imply this
correction touched a canon file, and it did not.

**That third line is also load-bearing because it replaces an earlier, wrong
claim.**
The first candidate said in places that Canon files were untouched. They
were not: `docs/canonical/canon-version.json` was modified in the 0.16.0
round, widening `repository_compatibility` from `>=0.1.0 <0.16.0` to
`>=0.1.0 <0.17.0`. That change is correct under the repository's versioning
rules, is **not** reverted, and is bookkeeping rather than semantics — but a
document that claims a modified file was untouched is wrong in a way that
costs a reader their trust in every other claim it makes. The wording above
is exact for that reason. §6 records the file-level detail.

This is the expected outcome and not a convenient one. PACK-16D implements
a model three earlier rounds already specified; if implementing that model
had required a new canon aggregate, the specification rounds would have
been incomplete, and saying so would have been the point of this document.
The corrections added threshold guardians and checkpoint signatures — the
two most plausible candidates for forcing an amendment — and §3 explains why
neither did. The final correction changed _how_ a signature is computed and
_how_ a parameter's provenance is recorded. Neither is a domain question: a
signature that verifies under the same key over the same bytes is the same
signature whoever's arithmetic produced it, and provenance metadata
describes where a constant came from rather than what it means. Swapping an
implementation for a library is the clearest possible case of a change that
is invisible to canon, and it is recorded here precisely so that the
reasoning is on file rather than assumed.

| ID      | Rule                                                                                                                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CA-01` | **A canon amendment is a decision, not a side effect of writing code.** If an implementation needs an aggregate the canon does not have, the correct output is a proposal in this document — never a quiet addition |
| `CA-02` | **This round produced no such proposal.** Every implementation entity maps onto an aggregate PACK-16A, PACK-16B or PACK-16C already specified, or is a service-level type on an established precedent               |

## 2. The eight entities §54 names

Each was checked by reading the implementation type and the canon
aggregate it claims to realise, not by matching names.

| ID      | Canon / specified aggregate             | Implementation type                                                                                      | Module                                                        | Verdict                                                                                                           |
| ------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `CA-03` | `AnonymousContinuationState` (PACK-16C) | `ContinuationState`                                                                                      | `casting/continuation.py`                                     | **Existing.** Three booleans and a capability reference, exactly the state PACK-16C specifies. No field was added |
| `CA-04` | `EncryptedBallotRecord`                 | `BallotEnvelope`, persisted in `ReferenceStore.accepted_ballots`                                         | `casting/ballot.py`, `casting/store.py`                       | **Existing.** The envelope's six fields are the specified ones; it carries no identity                            |
| `CA-05` | `SpoiledBallotRecord`                   | `BallotEnvelope` plus `BallotOpening`, persisted in `ReferenceStore.spoiled_ballots`                     | `casting/ballot.py`                                           | **Existing.** A spoiled record is the same envelope plus its opening, as specified                                |
| `CA-06` | `BatchLeafReservation`                  | `LeafReservation`                                                                                        | `casting/store.py`                                            | **Existing.** Anonymous, carries a submission reference and never a capability (`DM-10`)                          |
| `CA-07` | `PublicationObligation`                 | `PublicationObligation`                                                                                  | `publication/outbox.py`                                       | **Existing.** Same name, same role, and `FORBIDDEN_OUTBOX_FIELDS` enforces the specified exclusions               |
| `CA-08` | `BulletinBoardEntry`                    | `BoardEntry`, with `Checkpoint` as the checkpoint entry's payload                                        | `publication/bulletin_board.py`                               | **Existing.** The entry-type catalogue is PACK-16C's `BE-*`; no type was added                                    |
| `CA-09` | `ElectionRecordArtifact`                | `ElectionRecord`, `SealedBatch`, `BatchOpening`, `ReconciliationRecord`, `ContestTally`, `GuardianShare` | `election_record/builder.py`, `publication/sealed_batches.py` | **Existing.** These are the record's specified components, not new aggregates                                     |
| `CA-10` | `VerificationResult`                    | `VerificationResult`                                                                                     | `verification/results.py`                                     | **Existing.** Same name and role; the result-code set is PACK-16C's                                               |

## 3. Implementation types that are NOT canon aggregates

Nine types exist in the reference package that correspond to no canon
aggregate. Each is a service-level implementation concern, and each is
listed here rather than left for a reviewer to find.

| ID       | Type                                                                     | Module                              | Why it is not canon                                                                                                                                                                                                                                                                                                                                                                                                           |
| -------- | ------------------------------------------------------------------------ | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CA-11`  | `AuditRecord` / `AuditLog`                                               | `audit.py`                          | Operational evidence about the reference implementation's own behaviour. It is not election-record material, is never published, and holds nothing a canon consumer could read                                                                                                                                                                                                                                                |
| `CA-12`  | `FeatureFlags`                                                           | `invariants.py`                     | Configuration. It exists to make a class of misconfiguration impossible, not to model anything in the domain                                                                                                                                                                                                                                                                                                                  |
| `CA-13`  | `LogRecord`                                                              | `logging_boundary.py`               | A logging-transport type whose entire purpose is to _exclude_ domain data                                                                                                                                                                                                                                                                                                                                                     |
| `CA-14`  | `SchemaDescriptor`                                                       | `schemas.py`                        | Metadata about wire formats. It describes canon artefacts; it is not one                                                                                                                                                                                                                                                                                                                                                      |
| `CA-15`  | `FaultPoint` / `FaultInjector`                                           | `testing/faults.py`                 | Test-only. Production code depends on the `hooks.FaultHook` protocol and never imports these, which a test enforces with `ast`                                                                                                                                                                                                                                                                                                |
| `CA-15a` | `GuardianRecord`, `GuardianSecret`, `CeremonyTranscript`, `QuorumPolicy` | `guardians/ceremony.py`             | **New this correction.** A guardian roster is a cryptographic protocol artefact of one election, produced and consumed inside the voting service. No other bounded context reads it, and it has no lifecycle a canon consumer observes. `GuardianSecret` in particular must never leave the service, which settles the question by itself                                                                                     |
| `CA-15b` | `ThresholdShare`                                                         | `guardians/threshold.py`            | **New this correction.** A component of the election record's decryption evidence, on the same footing as `GuardianShare` (`CA-09`) — part of a specified artefact, not an aggregate of its own                                                                                                                                                                                                                               |
| `CA-15c` | `SignerRecord`, `SignerRegistry`, `CheckpointPayload`                    | `publication/checkpoint_signing.py` | **New this correction.** These describe _who may sign the board_, which is an operational trust configuration of the publication service. The registry is deliberately supplied out of band rather than modelled in the published record, and `OD-P16D-12` records that its own authorisation is a governance question — which is precisely an argument for keeping it out of canon until governance decides how it is issued |
| `CA-15d` | `ConformanceVector`, `EvidenceClass`                                     | `testing/conformance.py`            | Test evidence metadata. It describes how a value was checked, and is never part of an election record                                                                                                                                                                                                                                                                                                                         |
| `CA-15e` | `CheckpointSignatureProvider`, `CryptographyEd25519Provider`             | `crypto/signature_provider.py`      | **New this correction.** A port over a cryptographic library. It is infrastructure in the most literal sense: it answers whether bytes verify under a key and has no domain vocabulary at all. The canon-adjacent question — _whose_ key is authorised — is deliberately not its concern and lives in `SignerRegistry` (`CA-15c`), which is where the amendment question was already asked and answered                       |

| ID       | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CA-16`  | **The precedent for holding these at service level is established, not invented here.** PACK-12 held `PrivilegedSession` at service level, PACK-14 held `SessionRecord`, and PACK-15 held the voting context registry. All three rounds recorded the same reasoning: a type that no other bounded context reads is not a canon aggregate                                                                                                                                                  |
| `CA-16a` | **The correction's new types were tested against that rule, not waved past it.** The one that came closest to failing is `SignerRegistry`: a published, governance-issued signer set _would_ be canon-visible, because a verifier operator outside this service must obtain it. It is not canon **yet** precisely because no governance act issues it yet. If `OD-P16D-12` closes with a published registry, the amendment question must be re-asked — and this line exists so that it is |

## 4. Vocabulary check

`CA-17` — **No implementation name collides with a canon term meaning
something else.** Two were checked specifically because the words are
canon-adjacent:

- `ContestTally` is a per-option aggregate inside the election record. It
  is not the canon `Tally` concept of a completed, certified result, and
  it is never published outside a record.
- `AuditRecord` is not the canon audit-stream event of PACK-15. The two
  live in different contexts and share no field; the name is reused
  because it is the accurate English word, and this note exists so the
  reuse is deliberate rather than accidental.

## 5. What would have forced an amendment, and did not happen

`CA-18` — Stating the negative case explicitly, so the conclusion is
falsifiable rather than merely asserted. Any one of these would have
required a canon proposal:

| Would have required an amendment                                          | Did it happen?                                           |
| ------------------------------------------------------------------------- | -------------------------------------------------------- |
| A new aggregate with its own lifecycle that another bounded context reads | No                                                       |
| A new status value on an existing canon aggregate                         | No                                                       |
| A new domain event, or a new payload field on one                         | No — this round publishes no domain event at all         |
| A change to an existing aggregate's identity or relationships             | No                                                       |
| A canon-visible reinterpretation of an existing field                     | No                                                       |
| A guardian roster or quorum becoming an aggregate another context reads   | No — it stays inside the voting service (`CA-15a`)       |
| A signer registry published as part of the canon-visible record           | No — it is supplied out of band (`CA-15c`, `OD-P16D-12`) |

`CA-18a` — **`ElectionRecord` gained two fields this correction**
(`ceremony` and `threshold_shares`), and `BoardExport` gained two
(`signed_checkpoints`, `signer_registry`). Neither is a canon aggregate:
`ElectionRecordArtifact` is a specified composite (`CA-09`) whose component
list PACK-16A and PACK-16C already anticipated for a threshold tally, and
`BoardExport` is a transport container, not a domain object. Adding a
component to a specified composite is implementation; adding a _new_
composite would not have been.

## 6. Canon-version bookkeeping

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CA-19` | `canon_version` in `docs/canonical/canon-version.json` is **unchanged at `0.8.0`**                                                                                                                                                                                                                                                                                                                                                    |
| `CA-20` | `repository_compatibility` was widened from `>=0.1.0 <0.16.0` to `>=0.1.0 <0.17.0`. This is **non-canonical bookkeeping**: it records which repository versions can read canon 0.8.0, and the repository moved to `0.16.0`. Leaving it would have made the repository fail its own compatibility check about a canon this round did not touch                                                                                         |
| `CA-21` | `amended_at_repository_version` and `minimum_repository_version` are **unchanged at `0.9.0`**. They record when the 0.8.0 amendment happened and must never drift with a later round                                                                                                                                                                                                                                                  |
| `CA-22` | `scripts/check_canon_0_8_0.py` reports `OK: all 18 canon 0.8.0 amendment checks passed` after the bump, and reports it again unchanged after this correction                                                                                                                                                                                                                                                                          |
| `CA-23` | **No correction — first, second or third — modified any file under `docs/canonical/`.** `canon-version.json` still carries the 0.16.0 round's widened `repository_compatibility`; nothing further was needed, because `REPOSITORY_VERSION` did not move. That is a statement about this pass only — `CA-20` remains the accurate account of the entry's history, and neither statement may be compressed into "Canon files untouched" |

## 7. What this document does not decide

```text
Whether ADR-099/100/101/102 are accepted    → external review, PACK-17
Whether the model itself is correct          → PACK-16A/16B/16C review
Any future canon amendment                   → a later round, with a proposal
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
