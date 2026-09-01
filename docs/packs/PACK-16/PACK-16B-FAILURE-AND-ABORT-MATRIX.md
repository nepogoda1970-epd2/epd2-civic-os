# PACK-16B — Failure and Abort Matrix

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

**This matrix extends `PACK-16A-FAILURE-AND-ABORT-MODEL.md` (`FM-P16A-01`…
`FM-P16A-25`) into the ceremony and key-management domain.** No PACK-16A
condition is redefined; the `FM-16B-*` namespace is disjoint from
`FM-P16A-*`.

---

## 0. The outcome vocabulary

| Outcome              | Meaning                                                                                            |
| -------------------- | -------------------------------------------------------------------------------------------------- |
| **reject**           | The individual input or act is refused. The ceremony continues                                     |
| **retry**            | The same act may be attempted again, within a published bound                                      |
| **pause**            | The ceremony halts with state retained, pending a decision                                         |
| **restart ceremony** | The ceremony restarts from phase 6 with **all material destroyed** (`GL-16`); the context survives |
| **discard context**  | The election context is abandoned; a re-run is a **new** context with new keys                     |
| **abort**            | The ceremony ends now, material destroyed, nothing is carried forward                              |
| **annul**            | An **activated** context's result is voided; ballots are never decrypted (`CM-19`)                 |
| **block activation** | The activation lock (phase 20) may not be set; everything before it stands                         |

```text
An outcome is never chosen at the time by the person affected by it.
Each row below fixes it in advance, which is the only moment at which
it can be chosen honestly.
```

| ID          | Rule                                                                                                                                                          |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FM-16B-00` | **No condition in this matrix has "governance decides" as its outcome.** Where governance acts, it chooses between **named, bounded** alternatives fixed here |

---

## 1. Parameter conditions

| ID          | Condition                                                         | Detected at                      | Outcome                                                                                                                    | Reason code                                                                                       | Notes                                                          |
| ----------- | ----------------------------------------------------------------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `FM-16B-01` | **Unsupported parameter set**                                     | Any component, at load           | **reject** + **block activation** if at phase 1–2                                                                          | `parameter_set.unsupported`                                                                       | The component refuses to operate. It never falls back          |
| `FM-16B-02` | **Deprecated parameter set**                                      | Registry check, continuously     | **reject** for **new** contexts; running contexts continue to their published end; **block activation** of any new context | `parameter_set.deprecated`                                                                        | `CA-14` lineage — deprecation does not void a running election |
| `FM-16B-03` | **Prohibited parameter set**                                      | Registry check; emergency notice | **abort** if pre-activation; **annul** if in flight after an emergency prohibition                                         | `parameter_set.prohibited`                                                                        | The bounded alternatives are exactly these two; nothing else   |
| `FM-16B-04` | **Parameter mismatch** (component vs. manifest vs. pinned digest) | Startup and every ceremony phase | **reject** and **pause**; ceremony does not advance                                                                        | `parameter_set.digest_mismatch`, `parameter_set.modulus_mismatch`, `parameter_set.order_mismatch` | A mismatch is never reconciled at runtime                      |
| `FM-16B-07` | **Invalid generator**                                             | Parameter validation             | **reject** and **abort**                                                                                                   | `parameter_set.generator_mismatch`                                                                | `g` is fixed; a different `g` is a different system            |
| `FM-16B-08` | **Invalid subgroup / membership failure**                         | Every received group element     | **reject** the value; **pause** if it came from a guardian                                                                 | `parameter_set.membership_failed`                                                                 | Validation is mandatory on every input, not sampled            |

---

## 2. Randomness conditions

| ID          | Condition                                                                                                                       | Detected at                                | Outcome                                                                                                                            | Reason code                                                                                 | Notes                                                                           |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `FM-16B-05` | **Weak or unhealthy randomness — ceremony device**                                                                              | Health test before and during the ceremony | Before start: ceremony **does not start**. Mid-ceremony: **abort**, material destroyed, **restart ceremony**                       | `ceremony.randomness_health_failed`, `ceremony.randomness_degraded`, `crypto.reseed_failed` | `RN-14`…`RN-17`. There is no degraded mode                                      |
| `FM-16B-06` | **Weak or insufficient randomness — voting client**                                                                             | Client startup self-test                   | **reject** — the client refuses to encrypt; the participant is offered another device or the fallback channel                      | `ballot.randomness_insufficient`                                                            | Fail-closed. No ballot is produced                                              |
| `FM-16B-23` | **Guardian compromise confirmed** (incl. detected nonce reuse)                                                                  | Investigation; `RN-19` detection           | Pre-activation: **restart ceremony** without that guardian. Post-activation: **annul** the context — the bounded pair, per `CM` §4 | `guardian.compromise_confirmed`, `crypto.nonce_reuse_detected`                              | The choice between the two is determined by activation state, not by preference |
| `FM-16B-24` | **Test/rehearsal separation violation** — a deterministic seed, test key or rehearsal transcript reachable in a production path | Build review; runtime assertion            | **block activation**; if found after activation, **annul**                                                                         | `crypto.test_mode_reachable`                                                                | `KY-28`, `KY-32`, `CM-21`. A rehearsal transcript can never activate            |

---

## 3. Guardian-set conditions

| ID          | Condition                                    | Detected at              | Outcome                                                                                                                                                            | Reason code                                                                | Notes                                                                       |
| ----------- | -------------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `FM-16B-09` | **Invalid proof of possession**              | Phase 8                  | **reject** the contribution; **pause**; complaint opens; guardian **disqualified** if unremedied within the phase                                                  | `dkg.proof_of_possession_invalid`                                          | Arithmetic, so not adjudicated — `CD-09`                                    |
| `FM-16B-10` | **Duplicate guardian**                       | Phase 3–4                | **reject** the nomination; ceremony **does not start**                                                                                                             | `guardian_independence.duplicate_guardian`                                 | `GQ-02`                                                                     |
| `FM-16B-11` | **Non-independent guardian**                 | Phase 4; later discovery | Hard test: ceremony **does not start**, or **restart ceremony** if already begun. Soft test: **pause** and published Board assessment                              | `guardian_independence.hard_failure`, `guardian_independence.soft_failure` | The hard/soft split is `GI-01`…`GI-08` and is not re-litigated per ceremony |
| `FM-16B-15` | **Guardian disappearance** before activation | Waiting period expiry    | **pause**; then **restart ceremony** without them if before phase 14; **discard context** if after phase 14 and the set falls below `n` minimum                    | `guardian.disappeared`                                                     | `CD-30` governs the post-joint-key case                                     |
| `FM-16B-26` | **Post-activation guardian change attempt**  | Any time after phase 20  | **reject**, and the attempt is an incident. `k`, `n` and the guardian set are immutable for the context                                                            | `guardian.change_after_activation_refused`                                 | `GQ-04`, `RS-16B-12`                                                        |
| `FM-16B-31` | **Guardian compromise suspected**            | Any time                 | **pause** the guardian's participation; **notify** (`IN-14`); the Board classifies within a published period; outcome is then `FM-16B-23` or a published clearance | `guardian.compromise_suspected`                                            | Suspicion never itself annuls anything                                      |

---

## 4. Share and complaint conditions

| ID          | Condition                                      | Detected at             | Outcome                                                                                                                                                                       | Reason code                                               | Notes                                                           |
| ----------- | ---------------------------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------- |
| `FM-16B-12` | **Share delivery failure**                     | Phase 10–11             | **retry**, bounded to the published phase deadline; then **pause** and a complaint opens                                                                                      | `share_distribution.failed`, `share_distribution.missing` | A delivery failure is not by itself misconduct                  |
| `FM-16B-13` | **Share verification failure**                 | Phase 11                | **reject** the share; complaint opens; adjudication under `CD` §5 (single-share opening); the losing party is **disqualified**                                                | `share_verification.failed`                               | The one genuinely adjudicated failure                           |
| `FM-16B-14` | **Unresolved complaint** at the phase-12 close | Phase 12                | **pause** — the ceremony may not advance to phase 13 with an open complaint (`CD-07`)                                                                                         | `complaint.unresolved`                                    | No timeout resolves a complaint favourably                      |
| `FM-16B-27` | **Third failed ceremony attempt**              | Phase 6 restart counter | **discard context** and escalate to governance, whose bounded choices are: hold the vote by another means, re-run with a materially different guardian set, or do not hold it | `ceremony.restart_limit_reached`                          | `CD-33`. Repeated failure is a signal, not a scheduling problem |

---

## 5. Transcript, key and audit conditions

| ID          | Condition                                  | Detected at                                | Outcome                                                                                                                                                 | Reason code                                                            | Notes                                                                             |
| ----------- | ------------------------------------------ | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `FM-16B-16` | **Transcript split view**                  | Cross-location comparison; any verifier    | **pause immediately**; publish both views in full; **restart ceremony** unless the divergence is fully explained and both views reconcile to one record | `transcript.split_view_detected`                                       | `RC-07`, `RC-08`, `T-P16A-14`. A split view is never "resolved" by choosing one   |
| `FM-16B-17` | **Joint-key mismatch**                     | Phase 14; any recomputation                | **abort**. The joint key is the one artefact that cannot be partially right                                                                             | `joint_key.mismatch`                                                   | `KY-19` lineage                                                                   |
| `FM-16B-18` | **Auditor refusal**                        | Phase 17                                   | **block activation.** The Board may not overrule; its bounded choices are to remedy the auditor's finding and re-verify, or to abandon the context      | `ceremony.auditor_refusal`                                             | An auditor who can be overruled is not independent                                |
| `FM-16B-19` | **Decryption-share verification failure**  | Decryption ceremony                        | **halt the tally.** The share is **not dropped**; no result is produced until the failure is explained (`KC-10`, `BM-23`)                               | `decryption.share_invalid`                                             | The tempting error — quietly excluding a bad share — is exactly what is forbidden |
| `FM-16B-20` | **Quorum shortfall** (margin reaches 1)    | Continuously                               | **notify** (`IN-12`); ceremony continues; the Board must publish what it will do if one more is lost                                                    | `quorum.shortfall`                                                     | A warning state, not a failure state                                              |
| `FM-16B-32` | **Quorum lost** (fewer than `k` available) | Declaration after `CM-15` recovery attempt | Pre-activation: **discard context**. Post-closure: **annul**; the result is unobtainable and is announced as such                                       | `quorum.lost`                                                          | `CM-14`…`CM-19`. There is no third option, and inventing one is `FM-16B-21`       |
| `FM-16B-33` | **Archive verification failure**           | Scheduled re-verification                  | **pause** the archive's published integrity claim; investigate; publish the finding. **Never** re-derive the archive from a live system                 | `archive_verification.failed`, `archive_verification.evidence_missing` | A failed archive check is published, not repaired quietly                         |

---

## 6. Boundary-violation conditions — the ones that are not operational faults

These are not failures of a ceremony. They are failures of a **design or a
person**, and their outcomes are deliberately harsh.

| ID          | Condition                                                                                                                                  | Detected at                               | Outcome                                                                                                                                       | Reason code                                                                   | Notes                                                                    |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `FM-16B-21` | **Backup-policy violation** — any arrangement outside `BR-01`…`BR-08`, including any proposal to add compensation, escrow or split custody | Design review; custody declaration; audit | **Design review: rejection.** Operationally: **block activation** until removed; if found after activation, **annul**                         | `backup.policy_violation`, `crypto_agility.change_refused`                    | `BR-09`…`BR-12`. Rejected, not risk-accepted                             |
| `FM-16B-22` | **Hidden-master-key detection** — any capability by which fewer than `k` parties can decrypt                                               | Any time                                  | **block activation** before activation; **annul** after. In both cases a **published finding** naming the capability and how it came to exist | `backup.policy_violation`, `recovery.prohibited_path_refused`                 | The most serious finding this architecture admits                        |
| `FM-16B-25` | **Pre-closure decryption attempt**                                                                                                         | Any time before `voting_closed`           | **abort and annul.** The attempt is evidence of either a defect or an intent, and both are disqualifying                                      | `decryption.pre_closure_refused`, `decryption.authority_invalid`              | `CM-20`…`CM-23`. No investigation outcome makes the context usable again |
| `FM-16B-34` | **Downgrade attempt** — a weaker parameter set offered, selected or silently accepted                                                      | Any component                             | **reject** and **block activation**; published as a security finding                                                                          | `crypto_downgrade.attempt_detected`, `crypto_downgrade.pinned_digest_ignored` | There is no negotiation to lose, because there is no negotiation         |
| `FM-16B-35` | **Unauthorised transcript append** — an append by a role that may not append                                                               | Transcript verification                   | **reject**; treat as `FM-16B-16` if the record diverged                                                                                       | `transcript.append_refused`                                                   | `RS-16B-10`                                                              |

---

## 7. Device and software conditions

| ID          | Condition                                                                               | Detected at                  | Outcome                                                                                                                                                                                                                        | Reason code                       | Notes                                                 |
| ----------- | --------------------------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------- | ----------------------------------------------------- |
| `FM-16B-28` | **HSM attestation failure**                                                             | Phase 5; before each session | That guardian **does not participate** in the session; **pause** if the set falls below `k`; the failure is published                                                                                                          | `guardian.hsm_attestation_failed` | A failed attestation is not waived "for this session" |
| `FM-16B-29` | **Firmware trust failure** — trust cannot be established, or is withdrawn by the signer | Phase 5; advisory intake     | Pre-ceremony: guardian **does not participate** until remedied. Mid-ceremony: **pause**; the Board's bounded choices are to continue without that guardian (if `≥ k` remain and independence holds) or to **restart ceremony** | `guardian.firmware_trust_failed`  | `KU-11`                                               |
| `FM-16B-30` | **Ceremony software mismatch** — a participant's build differs from the published one   | Phase 5–6                    | Ceremony **does not start**; if detected later, **restart ceremony**. A mismatched build's contributions are **not** accepted retrospectively                                                                                  | `ceremony.software_mismatch`      | `KY-03`. Reproducible-build evidence is the check     |

---

## 8. Every condition the round task requires, mapped

| Required condition                      | ID                                               |
| --------------------------------------- | ------------------------------------------------ |
| unsupported parameter set               | `FM-16B-01`                                      |
| deprecated parameter set                | `FM-16B-02`                                      |
| prohibited parameter set                | `FM-16B-03`                                      |
| parameter mismatch                      | `FM-16B-04`                                      |
| invalid generator                       | `FM-16B-07`                                      |
| invalid subgroup                        | `FM-16B-08`                                      |
| invalid proof of possession             | `FM-16B-09`                                      |
| weak randomness                         | `FM-16B-05`, `FM-16B-06`                         |
| duplicate guardian                      | `FM-16B-10`                                      |
| non-independent guardian                | `FM-16B-11`                                      |
| share delivery failure                  | `FM-16B-12`                                      |
| share verification failure              | `FM-16B-13`                                      |
| unresolved complaint                    | `FM-16B-14`                                      |
| guardian disappearance                  | `FM-16B-15`                                      |
| guardian compromise                     | `FM-16B-23` (confirmed), `FM-16B-31` (suspected) |
| transcript split view                   | `FM-16B-16`                                      |
| joint-key mismatch                      | `FM-16B-17`                                      |
| auditor refusal                         | `FM-16B-18`                                      |
| quorum shortfall                        | `FM-16B-20`                                      |
| backup-policy violation                 | `FM-16B-21`                                      |
| hidden-master-key detection             | `FM-16B-22`                                      |
| HSM attestation failure                 | `FM-16B-28`                                      |
| firmware trust failure                  | `FM-16B-29`                                      |
| ceremony software mismatch              | `FM-16B-30`                                      |
| post-activation guardian change attempt | `FM-16B-26`                                      |
| pre-closure decryption attempt          | `FM-16B-25`                                      |

**26 of 26 covered**, by 28 identifiers — two required conditions are split
because their handling genuinely differs:

```text
weak randomness      → FM-16B-05 (ceremony device)  +  FM-16B-06 (voting client)
guardian compromise  → FM-16B-31 (suspected)        +  FM-16B-23 (confirmed)
```

**Seven conditions are EPD²-added**, because the round task's list does not
cover them and leaving them unlisted would leave their outcome to whoever
met them first:

```text
FM-16B-19  decryption-share verification failure   (KC-10, BM-23)
FM-16B-24  test/rehearsal separation violation
FM-16B-27  third failed ceremony attempt
FM-16B-32  quorum lost (as distinct from shortfall)
FM-16B-33  archive verification failure
FM-16B-34  parameter downgrade attempt
FM-16B-35  unauthorised transcript append
```

```text
28 identifiers for the 26 required  +  7 EPD²-added  =  35 conditions
plus FM-16B-00, which is a rule about outcomes and not a condition.
```

---

## 9. Outcome census

Computed from the rows of §1–§7. A condition appears under more than one
outcome when its outcome depends on **when it is detected**, and every such
dependence is stated in its row — the activation lock is the boundary in
every case.

| Outcome              | Count | Conditions                                                                   |
| -------------------- | ----- | ---------------------------------------------------------------------------- |
| **reject**           | 13    | `01`, `02`, `04`, `06`, `07`, `08`, `09`, `10`, `13`, `21`, `26`, `34`, `35` |
| **retry**            | 1     | `12`                                                                         |
| **pause**            | 12    | `04`, `08`, `09`, `11`, `12`, `14`, `15`, `16`, `28`, `29`, `31`, `33`       |
| **restart ceremony** | 7     | `05`, `11`, `15`, `16`, `23`, `29`, `30`                                     |
| **discard context**  | 3     | `15`, `27`, `32`                                                             |
| **abort**            | 5     | `03`, `05`, `07`, `17`, `25`                                                 |
| **annul**            | 7     | `03`, `21`, `22`, `23`, `24`, `25`, `32`                                     |
| **block activation** | 7     | `01`, `02`, `18`, `21`, `22`, `24`, `34`                                     |

**Conditions with exactly one outcome: 20. Conditions whose outcome depends
on detection time: 15.** No condition has zero outcomes, and none has an
outcome that is not in the §0 vocabulary.

---

## 10. The three conditions with no automatic outcome, and their bounds

| Condition                                       | Why no single outcome                          | The **complete** list of permitted choices                                                                  |
| ----------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `FM-16B-18` auditor refusal                     | The remedy depends on the finding              | (a) remedy and re-verify; (b) abandon the context. **Overruling is not on the list**                        |
| `FM-16B-27` third failed attempt                | Repeated failure has causes outside the system | (a) hold the vote by another means; (b) re-run with a materially different guardian set; (c) do not hold it |
| `FM-16B-29` firmware trust failure mid-ceremony | Depends on how many guardians remain           | (a) continue without that guardian if `≥ k` remain and independence still holds; (b) restart ceremony       |

```text
Three conditions, eight permitted outcomes in total, all named.
"Governance decides" appears nowhere in this document.
```

---

## 11. What this document does not decide

```text
Detection implementation and assertion placement   → PACK-16D
Alerting thresholds and on-call routing            → PACK-16D, PACK-17
Sanctions against a person found at fault          → GOVERNANCE, LEGAL
Re-run scheduling and participant communication    → GOVERNANCE
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
