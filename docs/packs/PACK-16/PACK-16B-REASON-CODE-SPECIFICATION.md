# PACK-16B — Reason Code Specification

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**Specification-level namespaces only.** No registry is implemented, no code
is written, `tests/contract/test_reason_codes_registry.py` is not touched,
and the Canonical Schema Registry is not modified. These are the codes a
later round must register, with their meanings fixed now so they cannot
drift.

---

## 0. Two catalogues, one system

PACK-16A's codes are **participant-facing** and use `UPPER_SNAKE_CASE`:
`BALLOT_PREPARATION_RANDOMNESS_INSUFFICIENT` is shown to a voter, mapped to
a governed German text, and tells them what to do next.

PACK-16B's codes are **ceremony and operations facing** and use **lowercase
dotted** namespaces: `dkg.contribution_invalid` is emitted into a
transcript, an audit stream and a public notification, and tells a verifier
what failed.

```text
Neither catalogue replaces the other, and neither is renamed.
A code in one catalogue MAY map to a code in the other;
   the mapping is declared, and it is not automatic.
```

| ID       | Rule                                                                                                                                                        |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-C01` | **The two catalogues share no identifier.** A lowercase dotted code is never a participant-facing string, and a PACK-16A code never appears in a transcript |
| `RN-C02` | **Declared cross-catalogue mappings** are listed in §14 and nowhere else                                                                                    |
| `RN-C03` | PACK-16A's codes are **unchanged by this round.** Nothing here renames, retires or redefines one                                                            |

---

## 1. The invariants

```text
stable                — a code's meaning never changes; a new meaning is a new code
machine-readable      — lowercase, dot-separated, [a-z0-9_]+ segments, exactly two segments
privacy-safe          — no participant is identifiable from a code or its fields
non-secret-bearing    — no share, nonce, seed, polynomial coefficient, private key
non-key-bearing       — no key material of any kind, public or private, as a code field
non-ballot-bearing    — no ciphertext, no selection, no tally, no partial decryption value
publicly mappable     — every code has a public meaning and an audit meaning, and they agree
versioned             — registered through the Canonical Schema Registry in a later round
```

| ID       | Rule                                                                                                                                                                                                           |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-C04` | **There is no generic `CEREMONY_ERROR`, `CRYPTO_ERROR` or `GUARDIAN_ERROR`, and none may be added.** Where two failures differ in what anyone must do next, they are two codes (PACK-13 `P13-RSN-002` lineage) |
| `RN-C05` | A code's **structured fields are enumerated per namespace** in §2…§13. A field not listed there may not be attached                                                                                            |
| `RN-C06` | **`guardian_index` is a permitted field; `guardian_name` is not.** The index is the arithmetic identifier; the name lives in the published manifest, where it belongs                                          |
| `RN-C07` | **No code carries a free-text field that reaches a public channel.** Free text is transcript content under `CT-13`…`CT-17`, adjudicated, and never a code payload                                              |
| `RN-C08` | A code that reports a **verification failure names the check**, not the remedy. `share_verification.failed` with `check: eq_31`, never a "retry_needed" form                                                   |
| `RN-C09` | **No code asserts a prohibited claim** — none may contain `certified`, `compliant`, `production_ready`, `final`, `coercion_proof`, `verified_secure` or a synonym                                              |

### 1.1 Permitted field vocabulary — the closed list

```text
context_id            guardian_index        recipient_index
phase                 check                 equation_ref
parameter_set_id      specification_digest  domain_tag
severity              fm_id                 od_id
available_count       k                     n
occurred_at           coarsened             authority_role
evidence_ref          withheld_category     prior_code_ref
```

| ID       | Rule                                                                                                                                                                 |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-C10` | **This list is closed.** A namespace may use a subset; no namespace may invent a field. Extending the list is a specification change, not an implementation decision |

---

## 2. `parameter_set.*` — parameter validity

| Code                                    | Meaning                                                                       | Fields                                     |
| --------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------ |
| `parameter_set.not_approved`            | The parameter set is not the one the Election Board approved for this context | `context_id`, `parameter_set_id`           |
| `parameter_set.unsupported`             | The component does not implement the declared parameter set                   | `parameter_set_id`                         |
| `parameter_set.deprecated`              | In use past its published `deprecation_date`                                  | `parameter_set_id`, `occurred_at`          |
| `parameter_set.prohibited`              | In use past its `prohibition_date`, or under an emergency prohibition         | `parameter_set_id`, `authority_role`       |
| `parameter_set.digest_mismatch`         | The specification digest does not match the pinned value                      | `parameter_set_id`, `specification_digest` |
| `parameter_set.modulus_mismatch`        | `p` does not equal the fixed value                                            | `parameter_set_id`                         |
| `parameter_set.order_mismatch`          | `q` does not equal the fixed value                                            | `parameter_set_id`                         |
| `parameter_set.generator_mismatch`      | `g` does not equal the fixed value                                            | `parameter_set_id`                         |
| `parameter_set.cofactor_invalid`        | `r` fails its published relation to `p` and `q`                               | `parameter_set_id`                         |
| `parameter_set.group_invalid`           | A group-level validation routine failed                                       | `parameter_set_id`, `check`                |
| `parameter_set.membership_failed`       | A received value is not in the expected subgroup                              | `check`, `equation_ref`                    |
| `parameter_set.encoding_invalid`        | A value is not in the required fixed-length big-endian encoding               | `check`                                    |
| `parameter_set.randomness_insufficient` | The randomness requirement attached to the parameter set is not met           | `check`                                    |

---

## 3. `ceremony.*` — session lifecycle

| Code                                | Meaning                                                           | Fields                             |
| ----------------------------------- | ----------------------------------------------------------------- | ---------------------------------- |
| `ceremony.started`                  | The ceremony began at the announced time                          | `context_id`, `occurred_at`        |
| `ceremony.profile_not_approved`     | The election profile has no Board approval; phase 1 not satisfied | `context_id`                       |
| `ceremony.session_creation_failed`  | The session could not be created under the declared parameters    | `context_id`, `check`              |
| `ceremony.phase_blocked`            | A phase precondition is unmet; the ceremony does not advance      | `phase`, `check`                   |
| `ceremony.paused`                   | Paused by a permitted actor; state retained                       | `phase`, `authority_role`          |
| `ceremony.resumed`                  | Resumed after a pause, with the pause recorded                    | `phase`                            |
| `ceremony.aborted`                  | Aborted; material destroyed per `GL-16`                           | `phase`, `fm_id`, `authority_role` |
| `ceremony.restart_required`         | A restart from phase 6 is required                                | `fm_id`                            |
| `ceremony.restart_limit_reached`    | The third failed attempt; escalates to governance (`CD-33`)       | `context_id`, `fm_id`              |
| `ceremony.completed`                | All twenty phases completed and checkpointed                      | `context_id`, `occurred_at`        |
| `ceremony.auditor_refusal`          | The Independent Auditor declined to attest the ceremony           | `phase`, `evidence_ref`            |
| `ceremony.board_refusal`            | The Election Board declined to accept the ceremony                | `phase`, `evidence_ref`            |
| `ceremony.randomness_health_failed` | A ceremony device's health test failed before starting            | `guardian_index`, `check`          |
| `ceremony.randomness_degraded`      | A health test failed mid-ceremony; abort                          | `guardian_index`, `fm_id`          |
| `ceremony.software_mismatch`        | A participant's build does not match the published ceremony build | `guardian_index`, `check`          |
| `ceremony.form_violation`           | The ceremony form used is looser than the one declared (`RC-15`)  | `phase`, `authority_role`          |

---

## 4. `guardian.*` — the person and their standing

| Code                                       | Meaning                                                           | Fields                                         |
| ------------------------------------------ | ----------------------------------------------------------------- | ---------------------------------------------- |
| `guardian.nominated`                       | A guardian was nominated and published                            | `context_id`, `guardian_index`                 |
| `guardian.nomination_refused`              | A nomination was refused at due diligence                         | `guardian_index`, `check`                      |
| `guardian.replaced_before_ceremony`        | Replaced before phase 5, with a published reason                  | `guardian_index`                               |
| `guardian.withdrew`                        | Withdrew voluntarily before activation                            | `guardian_index`, `phase`                      |
| `guardian.unavailable`                     | Known to be unavailable for a session                             | `guardian_index`, `phase`                      |
| `guardian.disappeared`                     | Unreachable past the published waiting period                     | `guardian_index`, `occurred_at`                |
| `guardian.compromise_suspected`            | A suspicion exists, with a severity class                         | `guardian_index`, `severity`                   |
| `guardian.compromise_confirmed`            | The Election Board has confirmed a compromise                     | `guardian_index`, `severity`, `authority_role` |
| `guardian.suspicion_withdrawn`             | A suspicion was withdrawn; the person is cleared (`IN-30`)        | `guardian_index`, `prior_code_ref`             |
| `guardian.retired`                         | Retired with material destroyed and attested (`GL-17`)            | `guardian_index`                               |
| `guardian.custody_declaration_missing`     | No custody class declared; ceremony does not start                | `guardian_index`                               |
| `guardian.hsm_attestation_failed`          | The declared hardware module failed attestation                   | `guardian_index`, `check`                      |
| `guardian.firmware_trust_failed`           | Declared firmware trust could not be established or was withdrawn | `guardian_index`, `check`                      |
| `guardian.change_after_activation_refused` | A change was attempted after the activation lock                  | `guardian_index`, `fm_id`                      |

---

## 5. `guardian_independence.*`

| Code                                              | Meaning                                                        | Fields                                       |
| ------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------- |
| `guardian_independence.hard_failure`              | A hard test failed; the set may not proceed                    | `check`, `guardian_index`, `recipient_index` |
| `guardian_independence.soft_failure`              | A soft test failed; assessed and published                     | `check`, `guardian_index`, `recipient_index` |
| `guardian_independence.violation_detected`        | A dependency was discovered after assessment                   | `check`, `guardian_index`                    |
| `guardian_independence.declaration_incomplete`    | A required declaration is missing                              | `guardian_index`, `check`                    |
| `guardian_independence.composition_failed`        | The set as a whole fails `GI-09`…`GI-13`                       | `check`                                      |
| `guardian_independence.duplicate_guardian`        | The same person or principal appears twice                     | `guardian_index`, `recipient_index`          |
| `guardian_independence.organization_interference` | An organization attempted to direct its guardian (`RS-16B-14`) | `guardian_index`                             |

---

## 6. `guardian_authentication.*`

| Code                                          | Meaning                                                                      | Fields                    |
| --------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------- |
| `guardian_authentication.failed`              | Authentication to the ceremony failed                                        | `guardian_index`, `phase` |
| `guardian_authentication.device_unattested`   | The device could not be attested and no witnessed provisioning record exists | `guardian_index`          |
| `guardian_authentication.device_mismatch`     | The device presented is not the declared device                              | `guardian_index`          |
| `guardian_authentication.witness_absent`      | The required independent observer is not present (`RC-02`)                   | `guardian_index`, `phase` |
| `guardian_authentication.remote_form_refused` | A fully remote participation attempt was refused                             | `guardian_index`, `fm_id` |

---

## 7. `dkg.*` — distributed key generation

| Code                              | Meaning                                                                    | Fields                           |
| --------------------------------- | -------------------------------------------------------------------------- | -------------------------------- |
| `dkg.contribution_invalid`        | A public contribution failed validation                                    | `guardian_index`, `equation_ref` |
| `dkg.proof_of_possession_invalid` | A Schnorr proof of possession failed                                       | `guardian_index`, `equation_ref` |
| `dkg.commitment_missing`          | A required polynomial commitment was not published                         | `guardian_index`, `phase`        |
| `dkg.commitment_invalid`          | A commitment failed its structural or membership check                     | `guardian_index`, `check`        |
| `dkg.pre_commitment_mismatch`     | The published contribution does not match the phase-9 commitment (`KY-11`) | `guardian_index`                 |
| `dkg.pre_commitment_missing`      | No commitment was published before the opening round                       | `guardian_index`                 |
| `dkg.kdf_failure`                 | A key-derivation step failed or produced an out-of-range value             | `check`                          |
| `dkg.contribution_late`           | A contribution arrived after the published phase deadline                  | `guardian_index`, `phase`        |

---

## 8. `share_distribution.*` and `share_verification.*`

| Code                                    | Meaning                                                          | Fields                                              |
| --------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------- |
| `share_distribution.failed`             | An encrypted share could not be delivered or published           | `guardian_index`, `recipient_index`                 |
| `share_distribution.missing`            | An expected share was never published                            | `guardian_index`, `recipient_index`, `phase`        |
| `share_distribution.duplicate`          | Two different shares were published for one ordered pair         | `guardian_index`, `recipient_index`                 |
| `share_distribution.encoding_invalid`   | The published share is not in the canonical encoding             | `guardian_index`, `recipient_index`                 |
| `share_verification.failed`             | A received share failed its verification equation                | `guardian_index`, `recipient_index`, `equation_ref` |
| `share_verification.decryption_failed`  | The recipient could not decrypt the share addressed to it        | `guardian_index`, `recipient_index`                 |
| `share_verification.not_performed`      | A recipient did not report a verification result by the deadline | `recipient_index`, `phase`                          |
| `share_verification.inconsistent_claim` | Sender and recipient claims contradict; adjudication required    | `guardian_index`, `recipient_index`                 |

---

## 9. `complaint.*` and `disqualification.*`

| Code                                       | Meaning                                                                     | Fields                                    |
| ------------------------------------------ | --------------------------------------------------------------------------- | ----------------------------------------- |
| `complaint.opened`                         | A signed complaint was published                                            | `guardian_index`, `phase`, `evidence_ref` |
| `complaint.unsigned_rejected`              | An unsigned submission is not a complaint (`CD-02`)                         | `phase`                                   |
| `complaint.answered`                       | The respondent answered within the deadline                                 | `guardian_index`, `evidence_ref`          |
| `complaint.uncontested`                    | The deadline passed without an answer (`CD-06`)                             | `guardian_index`                          |
| `complaint.upheld`                         | Adjudicated in the complainant's favour                                     | `guardian_index`, `authority_role`        |
| `complaint.dismissed`                      | Adjudicated against the complainant                                         | `guardian_index`, `authority_role`        |
| `complaint.unresolved`                     | Open past the phase-12 close; the ceremony may not advance                  | `guardian_index`, `fm_id`                 |
| `disqualification.recorded`                | A guardian was disqualified before activation                               | `guardian_index`, `authority_role`        |
| `disqualification.refused`                 | Disqualification was sought and refused                                     | `guardian_index`, `authority_role`        |
| `disqualification.after_joint_key_refused` | Disqualification sought after phase 14; a new context is required (`CD-30`) | `guardian_index`, `fm_id`                 |

---

## 10. `joint_key.*`

| Code                              | Meaning                                                           | Fields                       |
| --------------------------------- | ----------------------------------------------------------------- | ---------------------------- |
| `joint_key.published`             | The joint public key and its evidence were published              | `context_id`                 |
| `joint_key.mismatch`              | Independently recomputed joint key differs from the published one | `context_id`, `equation_ref` |
| `joint_key.incomplete_set`        | Fewer than `n` accepted contributions at phase 14                 | `context_id`, `n`            |
| `joint_key.recomputation_refused` | A verifier could not obtain the inputs needed to recompute        | `context_id`, `evidence_ref` |

---

## 11. `backup.*`, `recovery.*`, `compensation.*`

| Code                               | Meaning                                                                  | Fields                    |
| ---------------------------------- | ------------------------------------------------------------------------ | ------------------------- |
| `backup.declared`                  | A guardian declared holding a permitted own-share backup (`BR-05`)       | `guardian_index`          |
| `backup.declined`                  | A guardian declared holding none — permitted (`BR-07`)                   | `guardian_index`          |
| `backup.policy_violation`          | An arrangement outside `BR-01`…`BR-08` was proposed or found             | `guardian_index`, `fm_id` |
| `backup.destroyed`                 | Backup destroyed at retirement with attestation (`BR-06`)                | `guardian_index`          |
| `recovery.own_backup_used`         | A guardian restored their own share from their own backup                | `guardian_index`          |
| `recovery.not_possible`            | No recovery path exists for the situation reported                       | `guardian_index`, `fm_id` |
| `recovery.prohibited_path_refused` | A recovery outside a quorum ceremony was requested and refused (`KC-15`) | `authority_role`, `fm_id` |
| `compensation.not_applicable`      | **Terminal.** No compensation mechanism exists in this profile (`BR-13`) | `context_id`              |

| ID       | Rule                                                                                                                                                  |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-C11` | **`compensation.*` has exactly one member and it is terminal.** Any other `compensation.*` code is a design-boundary violation (`IN-33`, `FM-16B-21`) |

---

## 12. `quorum.*` and `decryption.*`

| Code                             | Meaning                                                            | Fields                                    |
| -------------------------------- | ------------------------------------------------------------------ | ----------------------------------------- |
| `quorum.shortfall`               | The available margin has reached 1 (`IN-12`)                       | `context_id`, `available_count`, `k`, `n` |
| `quorum.lost`                    | Fewer than `k` guardians are available; the result is unobtainable | `context_id`, `available_count`, `k`      |
| `quorum.reduction_refused`       | A request to lower `k` was refused (`GQ-05`, `RS-16B-12`)          | `authority_role`, `fm_id`                 |
| `quorum.composition_invalid`     | The available set violates an independence constraint              | `check`                                   |
| `decryption.ceremony_started`    | The decryption ceremony began, after `voting_closed`               | `context_id`, `occurred_at`               |
| `decryption.share_submitted`     | A partial decryption and its proof were published                  | `guardian_index`                          |
| `decryption.share_invalid`       | A partial decryption proof failed; the tally **halts** (`KC-10`)   | `guardian_index`, `equation_ref`, `fm_id` |
| `decryption.pre_closure_refused` | A decryption was attempted before closure and refused (`CM-20`)    | `authority_role`, `fm_id`                 |
| `decryption.authority_invalid`   | A decryption authorisation named a role that may not authorise it  | `authority_role`, `fm_id`                 |
| `decryption.completed`           | The decryption ceremony completed and the result was published     | `context_id`                              |

| ID       | Rule                                                                                                                                                                                                                |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-C12` | **No `decryption.*` code carries a value, a count, a margin or an aggregate.** `available_count` is permitted for quorum codes and prohibited for decryption codes — a partial count is a partial tally (`ADR-094`) |

---

## 13. `crypto_agility.*`, `crypto_downgrade.*`, `transcript.*`, `archive_verification.*`

| Code                                     | Meaning                                                              | Fields                               |
| ---------------------------------------- | -------------------------------------------------------------------- | ------------------------------------ |
| `crypto_agility.profile_registered`      | A new parameter profile was registered by the permitted authority    | `parameter_set_id`, `authority_role` |
| `crypto_agility.migration_scheduled`     | A dated migration was published                                      | `parameter_set_id`, `occurred_at`    |
| `crypto_agility.advisory_received`       | An upstream or external advisory was accepted into the intake        | `evidence_ref`                       |
| `crypto_agility.emergency_prohibition`   | A parameter set was prohibited with immediate effect                 | `parameter_set_id`, `authority_role` |
| `crypto_agility.change_refused`          | A parameter change was attempted by a party that may not make one    | `authority_role`, `fm_id`            |
| `crypto_downgrade.attempt_detected`      | A weaker parameter set was offered or selected                       | `parameter_set_id`, `fm_id`          |
| `crypto_downgrade.negotiation_refused`   | A component attempted parameter negotiation; refused by construction | `check`                              |
| `crypto_downgrade.pinned_digest_ignored` | A component proceeded without checking the pinned digest             | `specification_digest`, `fm_id`      |
| `transcript.checkpoint_failed`           | A checkpoint could not be produced or published                      | `phase`, `check`                     |
| `transcript.hash_mismatch`               | A transcript hash does not match its recomputation                   | `phase`, `equation_ref`              |
| `transcript.base_hash_mismatch`          | A base or extended base hash does not match                          | `context_id`, `equation_ref`         |
| `transcript.challenge_invalid`           | A Fiat–Shamir challenge does not recompute                           | `equation_ref`                       |
| `transcript.domain_separation_invalid`   | A domain tag is wrong, missing or reused                             | `domain_tag`                         |
| `transcript.encoding_non_canonical`      | A hashed input is not in the canonical fixed-length encoding         | `check`                              |
| `transcript.split_view_detected`         | Two published views of the transcript differ (`RC-08`)               | `phase`, `evidence_ref`              |
| `transcript.verification_failed`         | Independent verification of the transcript failed                    | `phase`, `evidence_ref`              |
| `transcript.append_refused`              | An append was attempted by a role that may not append (`RS-16B-10`)  | `authority_role`, `fm_id`            |
| `archive_verification.passed`            | A scheduled archive re-verification succeeded                        | `context_id`, `occurred_at`          |
| `archive_verification.failed`            | A scheduled archive re-verification failed                           | `context_id`, `check`, `fm_id`       |
| `archive_verification.evidence_missing`  | Referenced evidence is no longer retrievable                         | `evidence_ref`                       |
| `archive_verification.retention_expired` | Material reached its published destruction date and was destroyed    | `context_id`, `occurred_at`          |

---

## 14. Two additional declared namespaces, and the cross-catalogue mapping

The round task names twenty namespaces. Two more are used by this round's
documents and are declared here rather than left undeclared.

| Namespace  | Why it exists                                                                                                                                   |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `crypto.*` | Cross-cutting cryptographic hygiene that belongs to no single ceremony phase — it can occur in the client, the ceremony or a service            |
| `ballot.*` | The **operational** counterpart of PACK-16A's participant-facing ballot codes: what the audit stream records when the client refuses to encrypt |

| Code                             | Meaning                                                          | Fields           |
| -------------------------------- | ---------------------------------------------------------------- | ---------------- |
| `crypto.reseed_failed`           | A generator could not reseed after fork, resume or snapshot      | `check`          |
| `crypto.nonce_reuse_detected`    | A nonce repetition was detected; treated as confirmed compromise | `check`, `fm_id` |
| `crypto.test_mode_reachable`     | A deterministic or test path is reachable in a production build  | `check`, `fm_id` |
| `crypto.zeroization_failed`      | Secret material could not be zeroised where required             | `check`          |
| `ballot.randomness_insufficient` | The client's randomness self-test failed; encryption refused     | `check`          |

### 14.1 The declared mappings — the complete list

**The first column is the destination, so that no row of this table can be
mistaken for a code definition.** Every operational code below is defined
once, in §2–§14.

| PACK-16A participant-facing code                | Mapped from (PACK-16B operational)                           | Direction                    |
| ----------------------------------------------- | ------------------------------------------------------------ | ---------------------------- |
| `BALLOT_PREPARATION_RANDOMNESS_INSUFFICIENT`    | the `ballot.*` randomness-insufficient code                  | operational → participant    |
| `BALLOT_PREPARATION_PARAMETERS_REJECTED`        | the `parameter_set.*` not-approved and digest-mismatch codes | operational → participant    |
| `BALLOT_PREPARATION_PROFILE_UNSUPPORTED`        | the `parameter_set.*` unsupported code                       | operational → participant    |
| governed context-annulment text, **not a code** | the `quorum.*` lost code                                     | operational → published text |

| ID       | Rule                                                                                                                                                                                                   |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `RN-C13` | **The mapping is many-to-one and lossy on purpose.** A participant is told what to do; a verifier is told what failed. Enriching the participant-facing code with the operational detail is prohibited |
| `RN-C14` | **No ceremony namespace maps to a participant-facing code at all.** A voter is never shown `dkg.*`, `share_*`, `guardian*`, `quorum.*` or `decryption.*`                                               |

---

## 15. Uniqueness and registration

| ID       | Rule                                                                                                                                                          |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RN-C15` | **Every code in this document is unique.** Duplicate reason codes = 0 is a verification criterion of this round and is checked mechanically                   |
| `RN-C16` | Codes are registered through the **Canonical Schema Registry** in a later round; this document is the source, not the registry                                |
| `RN-C17` | **Retirement, never redefinition.** A code that ceases to be emitted is marked retired and its identifier is never reused                                     |
| `RN-C18` | A code emitted by a component that this round does not specify is **out of scope here** and may not be added by an implementer without a specification change |

### 15.1 Census — computed from the tables above

```text
Namespaces required by the round task     20   all present
Namespaces declared in addition            2   crypto.*, ballot.*  (§14)
Namespaces defined in total               22

Codes defined                            129
Duplicate code identifiers                 0
Codes used elsewhere in PACK-16B but
   not defined here                        0
```

Every code cited by any other PACK-16B document — and by `ADR-100` — is
defined here exactly once. §14.1's mapping table is deliberately written
with the participant-facing code first, so that no row of it can be
mistaken for, or counted as, a definition.

---

## 16. What this document does not decide

```text
Registry implementation and schema versioning     → PACK-16D, Canonical Schema Registry
The German participant-facing texts                → PACK-15 content catalogue lineage
Log transport, retention and alert routing         → PACK-16D, PACK-17
Which codes are alerted on out of hours            → GOVERNANCE
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
