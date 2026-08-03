# PACK-16B — Acceptance Matrix

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee Architecture. **Specification and ADR only. No code. No cryptographic code. Not implemented. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-100`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. How to read this matrix, and what a status means

Ten columns, one row per requirement. **`SATISFIED` here means "decided and
written down in this round", not "built", "tested" or "verified".** No
status in this document asserts that anything works.

| Status                  | Meaning                                                                                              |
| ----------------------- | ------------------------------------------------------------------------------------------------------ |
| `SATISFIED`             | The requirement is decided within this round, and the decision is recorded with its reasoning          |
| `PARTIALLY SATISFIED`   | Decided in part; the remainder is named, owned and dated                                              |
| `DEFERRED`              | Specified here, delivery owned by a named later round                                                 |
| `BLOCKED`               | Cannot be closed without a named **external** artefact that does not exist                            |
| `NOT APPLICABLE`        | The mechanism the requirement addresses does not exist in the selected profile — stated, not assumed  |
**`CORRECTED` is not an acceptance status and is not used here.** Where this
round corrected a PACK-16A statement of fact, the row carries the
**substantive** status the requirement actually reached, and the correction
is recorded in the row's decision cell.

**A `SATISFIED` row is not evidence of correctness.** The only rows that
speak to correctness are those pointing at `TV-01`…`TV-08`, and one of them
is `BLOCKED`.

---

## 2. The matrix

| Requirement ID | Requirement | PACK-16A source | External evidence | Decision document | Section | Decision | Status | Residual risk | Next stage |
| -------------- | ----------- | --------------- | ----------------- | ----------------- | ------- | -------- | ------ | ------------- | ---------- |
| `AC-P16B-001` | Threshold trust: decryption requires k of n, k > 1 always | `KC-01` | `[F-18]` | `PACK-16B-GUARDIAN-AND-QUORUM-MODEL.md` | §2, §5 | `k=3/n=5` default, `k=4/n=7` high assurance; `k ≥ 3` always | **SATISFIED** | none | — |
| `AC-P16B-002` | No single-admin decryption by any path | `KC-02` | `[F-11]` | `PACK-16B-GUARDIAN-AND-QUORUM-MODEL.md` · `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` · `PACK-16B-ROLE-SEPARATION-MATRIX.md` | `GQ-13`, `CM-18`, `RS-16B-13` | No principal, role, grant, flag or break-glass may assemble a quorum; the operation does not exist | **SATISFIED** | none architecturally; enforcement is `IM-*` | PACK-16D |
| `AC-P16B-003` | Minimum guardian count chosen on a stated principle | `KC-03` | `[F-18]` | `PACK-16B-GUARDIAN-AND-QUORUM-MODEL.md` | §3, `GQ-05` | `n ≥ 5`, `n ≤ 9`, `n ≥ k + 2`; survivability of `n − k` losses | **SATISFIED** | none | — |
| `AC-P16B-004` | Quorum chosen so one organisation cannot reach it | `KC-04` | `[F-18]` | `PACK-16B-GUARDIAN-AND-QUORUM-MODEL.md` | `GQ-01`, `GQ-11` | No organisation supplies `k`; internal guardians capped at `k − 1` | **SATISFIED** | organisational drift over time | GOVERNANCE |
| `AC-P16B-005` | Guardians drawn from organisationally distinct bodies | `KC-05` | — | `PACK-16B-GUARDIAN-INDEPENDENCE-MATRIX.md` | §2, `GQ-03` | 15 pairwise tests, hard/soft; composition tests `GI-09`…`GI-13` | **SATISFIED** | declarations are self-reported | GOVERNANCE |
| `AC-P16B-006` | Guardian authentication at ceremony assurance; no shared account | `KC-06` | — | `PACK-16B-KEY-CEREMONY-SPECIFICATION.md` · `PACK-16B-GUARDIAN-LIFECYCLE.md` | phase 5, `GL-06` | Per-guardian authentication and device attestation; `RS-16B-02` forbids shared principals | **SATISFIED** | attestation availability varies by class | PACK-16D |
| `AC-P16B-007` | Every ceremony step produces published verifiable evidence | `KC-07` | `[F-13]` | `PACK-16B-CEREMONY-TRANSCRIPT-SPECIFICATION.md` | `CT-01`…`CT-12` | 20 phases each produce a transcript entry with an attributable actor | **SATISFIED** | none | — |
| `AC-P16B-008` | Joint public key published with well-formedness proofs | `KC-08` | `[F-13]` | `PACK-16B-KEY-CEREMONY-SPECIFICATION.md` · `PACK-16B-CEREMONY-TRANSCRIPT-SPECIFICATION.md` | phase 14, `CT-09` | Schnorr proofs published; joint key independently recomputable | **SATISFIED** | none | — |
| `AC-P16B-009` | Polynomial commitments and share-distribution evidence published | `KC-09` | `[F-13]` | `PACK-16B-KEY-CEREMONY-SPECIFICATION.md` | §6.1, `KY-13`…`KY-16` | Encrypted shares are published, not merely transmitted | **SATISFIED** | none | — |
| `AC-P16B-010` | Decryption-share verification halts the tally on failure | `KC-10` | `[F-11]` | `PACK-16B-FAILURE-AND-ABORT-MATRIX.md` | `FM-16B-19` | A failing share halts the tally; it is never dropped | **SATISFIED** | none | PACK-16C |
| `AC-P16B-011` | Lost-trustee handling within the quorum; absence published | `KC-11` | `[F-11]` | `PACK-16B-SCOPE-AND-BOUNDARY.md` · `PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md` | SCOPE §5, BRC §5 | Absence within the quorum is handled by direct Lagrange over the available set, tolerance exactly `n − k`, and absence is published. **PACK-16A's description of the mechanism as compensated decryption was corrected against primary evidence; the requirement itself is unchanged and is met** | **SATISFIED** | none | — |
| `AC-P16B-012` | Compromised-trustee handling as a context-level event | `KC-12` | — | `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` | §3, §4 | Nine severity classes; bounded outcomes by activation state (`FM-16B-23`) | **SATISFIED** | detection depends on disclosure | PACK-17 |
| `AC-P16B-013` | Below quorum, the result is unobtainable — by design | `KC-13` | `[F-11]` | `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` | §5 | Declared after a documented recovery attempt; context annulled; ballots never decrypted | **SATISFIED** | the cost falls on participants | GOVERNANCE |
| `AC-P16B-014` | Backup may not reduce the threshold | `KC-14` | — | `PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md` | §2, §3 | Per-guardian, guardian-custodied backup of its own share only; four models prohibited | **SATISFIED** | guardian exposure surface doubles by choice | — |
| `AC-P16B-015` | No recovery outside a quorum ceremony | `KC-15` | `[F-11]` | `PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md` | §4, §6 | Complete recovery list; no authority may create another path | **SATISFIED** | none | — |
| `AC-P16B-016` | Security Admin and System Admin separation; neither holds guardian material | `KC-16` | — | `PACK-16B-ROLE-SEPARATION-MATRIX.md` | `RS-16B-04`, `RS-16B-05` | Structural: neither appears in the ceremony RACI at all | **SATISFIED** | none | — |
| `AC-P16B-017` | Out-of-band notification of ceremony events | `KC-17` | — | `PACK-16B-INCIDENT-AND-NOTIFICATION-MODEL.md` | §3, `IN-25`…`IN-29` | Registered and tested before phase 5; four events always out of band | **SATISFIED** | receipt may be unknown, and is recorded as such | PACK-16D |
| `AC-P16B-018` | No silent break-glass touching guardian material | `KC-18` | — | `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` · `PACK-16B-ROLE-SEPARATION-MATRIX.md` | §6, `RS-16B-11` | No break-glass exists; the Incident Commander authorises no decryption | **SATISFIED** | none | — |
| `AC-P16B-019` | Parameter provenance published and independently reproducible | `KC-19` | `[F-02]`, `[F-03]` | `PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md` | §6 | Derivation published upstream; regenerated and confirmed byte for byte by this round | **SATISFIED** | the reproduction is EPD²’s own | `TV-01`, PACK-16D |
| `AC-P16B-020` | Test key structurally incapable of validating in production | `KC-20` | — | `PACK-16B-KEY-CEREMONY-SPECIFICATION.md` · `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` | `KY-28`, `KY-32`, `CM-21` | Separate domains, separate context IDs, separate environment marker; `FM-16B-24` blocks activation | **PARTIALLY SATISFIED** | demonstration requires a build | PACK-16D |
| `AC-P16B-021` | Parameters justified against BSI TR-02102-1 (2026-01) | `KC-21` | `[F-36]`, `[F-20]`, `[F-21]`, `[F-25]`, `[F-33]`, `[F-34]`, `[F-35]` | `PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md` | §3, §3.2 | **`q = 256` bits exceeds the BSI minimum of 250 bits** for this parameter dimension — TR-02102-1 (2026-01) **§2.3.3 p. 34** and **§2.3.5 p. 36**, read first-hand `[F-36]`; `\|p\| = 4096 ≥ 3000` and `ord(g)` prime also satisfied | **SATISFIED** | This row does not establish complete BSI conformity or certification. One recommendation-level divergence is recorded — Remark 2.12's MODP/ffdhe published-parameter preference (`VO-08`), which **blocks production and legal activation** | `VO-08` — PACK-16B external cryptographic review, with independent confirmation in PACK-17 |
| `AC-P16B-022` | Record whether the integer-group choice is acceptable, or declare divergence | `KC-22` | `[F-21]`, `[F-23]` | `PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md` · `PACK-16B-PARAMETER-SET-SPECIFICATION.md` | §3, §2 | Acceptable on every verified figure; no key-length divergence to declare | **SATISFIED** | temporal divergence only — the 2031 horizon | `OD-P16B-06` |
| `AC-P16B-023` | Verify strong Fiat–Shamir by test, not assumption | `KC-23` | `[F-08]` | `PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md` · `PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` | `IM-07`, `TV-06` | The construction is strong FS upstream; the test is named and mandatory | **DEFERRED** | no implementation exists to test | PACK-16D |
| `AC-P16B-024` | Verify output against an independent verifier not shipped with it | `KC-24` | — | `PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` | `TV-07`, `VC-05` | Differential testing against an implementation EPD² did not write; blocking for activation | **DEFERRED** | a second implementation may not exist | PACK-16D |
| `AC-P16B-025` | Pin and record implementation version, provenance and supply chain | `KC-25` | — | `PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md` | `IM-33`…`IM-38` | Reproducible build, pinned digests, published attestation — all MANDATORY | **DEFERRED** | none at specification level | PACK-16D |
| `AC-P16B-026` | Where no implementation satisfies KC-23–KC-25, do not proceed | `KC-26` | — | `PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md` | `IM-02` | A mandatory failure is a rejection; no aggregate overrides it | **SATISFIED** | `RR-01` — no production-grade implementation exists | `OD-P16A-04` |
| `AC-P16B-027` | Migration path that does not require re-opening a past record | `KC-27` | `[F-05]`, `[F-25]` | `PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md` | `CA-06`…`CA-10`, `PS-10` | A successor is a new profile; verification capability is never withdrawn | **PARTIALLY SATISFIED** | `RB-02` — the successor does not exist yet | `OD-P16B-06` |
| `AC-P16B-028` | An exact parameter profile is selected or an honest blocker recorded | round §6 | `[F-04]` | `PACK-16B-PARAMETER-SET-SPECIFICATION.md` | §2 | `EPD2-CRYPTO-1` — Option A, unmodified upstream parameters | **SATISFIED** | none | — |
| `AC-P16B-029` | Finite-field versus elliptic-curve decision stated explicitly A/B/C/D | round §7 | `[F-04]`, `[F-05]`, `[F-07]`, `[F-23]` | `PACK-16B-PARAMETER-SET-SPECIFICATION.md` | §2 | Option A selected on a 16-row comparison; B and C are verifier-forking adaptations, not parameter choices | **SATISFIED** | none | — |
| `AC-P16B-030` | The decision is not made on performance grounds | round §7 | — | `PACK-16B-PARAMETER-SET-SPECIFICATION.md` · `PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md` | §2, `IM-46` | Performance is recorded and is explicitly non-decisive | **SATISFIED** | none | — |
| `AC-P16B-031` | Parameter registry with lifecycle and authority | round §10 | — | `PACK-16B-PARAMETER-SET-SPECIFICATION.md` | §3 | `CryptographicParameterSet` with statuses, dated transitions and an approving authority | **SATISFIED** | a registry of one entry | `CAM-P16B-02` |
| `AC-P16B-032` | Specification pinned by digest | round §10 | `[F-30]` | `PACK-16B-PARAMETER-SET-SPECIFICATION.md` · `PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md` | `PS-*`, `CA-01`…`CA-05` | SHA-256 pinned; a new digest is a new profile | **SATISFIED** | digest confirmed over one network path | `VO-04` |
| `AC-P16B-033` | Downgrade prohibited architecturally, not by policy | round §11 | `[F-05]` | `PACK-16B-PARAMETER-SET-SPECIFICATION.md` · `PACK-16B-FAILURE-AND-ABORT-MATRIX.md` | §5, `FM-16B-34` | No negotiation exists; a weaker set is refused and blocks activation | **SATISFIED** | none | — |
| `AC-P16B-034` | Emergency prohibition with bounded outcomes | round §11 | — | `PACK-16B-PARAMETER-SET-SPECIFICATION.md` | §5 | Abort pre-activation; annul in flight. Exactly two outcomes | **SATISFIED** | none | — |
| `AC-P16B-035` | Cryptographic agility: six kinds separated | round §11 | `[F-04]` | `PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md` | §1 | Parameter migration does not exist in this profile; algorithm migration is a new ADR | **SATISFIED** | none | — |
| `AC-P16B-036` | Who may and may not change parameters | round §11 | — | `PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md` | `CA-11`…`CA-13` | Election Board on a reviewer assessment; nobody else, categorically | **SATISFIED** | none | — |
| `AC-P16B-037` | Advisory intake operated by EPD² itself | round §11 | `[F-30]` | `PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md` | `CA-19`…`CA-23`, `CA-27` | EPD² maintains its own errata record because upstream has none | **SATISFIED** | depends on EPD² actually watching | GOVERNANCE |
| `AC-P16B-038` | German-guidance horizon converted into registry fields | round §6 | `[F-25]` | `PACK-16B-PARAMETER-SET-SPECIFICATION.md` · `PACK-16B-CRYPTOGRAPHIC-AGILITY-MODEL.md` | `PS-*`, `CA-08` | `deprecation_date` 2030/2031-12-31; `prohibition_date` 2032-12-31 | **SATISFIED** | `RB-02`, rated high | `OD-P16B-06` |
| `AC-P16B-039` | Security strength stated as an inference, not a quotation | round §5 | `[F-01]` | `PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md` | §4 | ≈128-bit generic DL strength, marked as inference; the source states none | **SATISFIED** | none | — |
| `AC-P16B-040` | BSI reading limitation recorded rather than papered over | round §5 | `[F-22]`, `[F-36]` | `PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md` | §3.2, §3.2.1 | Characterised exactly, with a full attempt log and two controls; **the limitation was then resolved by direct local supply of the official PDF, not worked around**, and `[F-36]` is a first-hand reading | **SATISFIED** | none — `RB-01` closed | — |
| `AC-P16B-041` | ElectionGuard compatibility assessed explicitly | round §6 | `[F-05]` | `PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md` · `PACK-16B-PARAMETER-SET-SPECIFICATION.md` | §2, §8 | **Expected specification compatibility, conditional on independent verifier testing** — no verifier-consumed field is changed; acceptance is not yet demonstrated | **SATISFIED** | interoperability is expected, not demonstrated | `TV-07`, `TV-19` |
| `AC-P16B-042` | Security proofs remain applicable under the selection | round §6 | `[F-17]` | `PACK-16B-CRYPTOGRAPHIC-PARAMETER-ASSESSMENT.md` | §8 | The published IND-CPA theorem applies as stated under Option A | **PARTIALLY SATISFIED** | not peer-reviewed independently `[F-31]` | `TV-08` |
| `AC-P16B-043` | What may be called ElectionGuard lineage after the selection | `OD-P16A-03` | `[F-04]` | `PACK-16B-PARAMETER-SET-SPECIFICATION.md` | §2 | Unmodified parameters, so the lineage claim is exact and needs no qualifier | **SATISFIED** | none | — |
| `AC-P16B-044` | EPD² additions change no verifier-consumed field | round §8 | `[F-08]`, `[F-16]` | `PACK-16B-KEY-CEREMONY-SPECIFICATION.md` · `PACK-16B-FIAT-SHAMIR-AND-DOMAIN-SEPARATION.md` | §4, §5 | Commitment round and complaints sit at the orchestration layer | **PARTIALLY SATISFIED** | requires external confirmation | `TV-08`, `TV-11` |
| `AC-P16B-045` | Fiat–Shamir transcript defined unambiguously | round §8 | `[F-06]`, `[F-08]` | `PACK-16B-FIAT-SHAMIR-AND-DOMAIN-SEPARATION.md` | §1…§3 | `FS-01`…`FS-15`; statement and context in every challenge | **SATISFIED** | none | — |
| `AC-P16B-046` | Domain separation defined completely | round §8 | `[F-09]` | `PACK-16B-FIAT-SHAMIR-AND-DOMAIN-SEPARATION.md` | §4, §5 | 27 upstream tags plus EPD² string tags under `H_X`; no tag-byte squatting | **SATISFIED** | none | `TV-06` |
| `AC-P16B-047` | Canonical encoding defined | round §8 | `[F-09]` | `PACK-16B-FIAT-SHAMIR-AND-DOMAIN-SEPARATION.md` | §4 | 512/32/4-byte fixed-length big-endian; non-canonical input rejected | **SATISFIED** | none | `TV-05` |
| `AC-P16B-048` | The two upstream specification inconsistencies resolved | round §8 | `[F-19]` | `PACK-16B-FIAT-SHAMIR-AND-DOMAIN-SEPARATION.md` | §7 | `0x32` → `H_I`; `0x44` without `"LOCK"`; `DS-16` defers if upstream differs | **PARTIALLY SATISFIED** | EPD²’s own reading, unconfirmed | `CA-27`, `TV-08` |
| `AC-P16B-049` | Transcript contents fixed, and prohibited contents fixed | round §16 | `[F-13]` | `PACK-16B-CEREMONY-TRANSCRIPT-SPECIFICATION.md` | §3, §4 | `CT-01`…`CT-29`; prohibited content enumerated | **SATISFIED** | none | — |
| `AC-P16B-050` | What a transcript reader can and cannot verify is published with it | round §16 | `[F-14]` | `PACK-16B-CEREMONY-TRANSCRIPT-SPECIFICATION.md` | §6 | A table published alongside the transcript | **SATISFIED** | non-repudiation limit is real and stated | — |
| `AC-P16B-051` | Split-view detection and response | round §33 | — | `PACK-16B-FAILURE-AND-ABORT-MATRIX.md` · `PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md` | `FM-16B-16`, `RC-07` | Per-location views compared before any checkpoint; divergence halts | **SATISFIED** | detection needs at least two views | — |
| `AC-P16B-052` | Randomness architecture defined against current guidance | round §9 | `[F-26]`…`[F-29]` | `PACK-16B-RANDOMNESS-ARCHITECTURE.md` | §1 | `EPD2-RND-1`; AIS 20/31 v3.0 classes with SP 800-90A/B/C | **SATISFIED** | which AIS class is required is `VO-02` | `VO-02` |
| `AC-P16B-053` | PTG.2 never used directly for key material | round §9 | `[F-26]` | `PACK-16B-RANDOMNESS-ARCHITECTURE.md` | `RN-02` | Physical sources seed a DRNG; they do not produce keys | **SATISFIED** | none | — |
| `AC-P16B-054` | Fail-closed on randomness failure | round §9 | — | `PACK-16B-RANDOMNESS-ARCHITECTURE.md` · `PACK-16B-FAILURE-AND-ABORT-MATRIX.md` | §6, `FM-16B-05`, `FM-16B-06` | No degraded mode; the client refuses to encrypt | **SATISFIED** | a silent nonce failure is undetectable by any verifier | `IM-43` |
| `AC-P16B-055` | Fork, snapshot and browser duplication hazards addressed | round §9 | — | `PACK-16B-RANDOMNESS-ARCHITECTURE.md` | §4 | Reseed on fork/resume/snapshot; virtualisation prohibited for ceremony devices | **SATISFIED** | browser entropy quality is not controllable | PACK-16D |
| `AC-P16B-056` | What cannot be verified about randomness is stated | round §9 | — | `PACK-16B-RANDOMNESS-ARCHITECTURE.md` | §7 | Stated plainly rather than implied | **SATISFIED** | — | — |
| `AC-P16B-057` | Guardian count and quorum chosen explicitly with a comparison | round §12 | `[F-18]` | `PACK-16B-GUARDIAN-AND-QUORUM-MODEL.md` | §3 | 2-of-3, 3-of-5, 4-of-7, 5-of-9 compared; 3-of-5 default, 4-of-7 high assurance | **SATISFIED** | none | — |
| `AC-P16B-058` | Organizational independence defined factually, not formally | round §13 | — | `PACK-16B-GUARDIAN-INDEPENDENCE-MATRIX.md` | §2, §3 | 15 pairwise tests with hard/soft classification and a collusion matrix | **SATISFIED** | assessment is judgement on soft tests | GOVERNANCE |
| `AC-P16B-059` | An HSM does not convert one administrator into a threshold | round §18 | — | `PACK-16B-GUARDIAN-INDEPENDENCE-MATRIX.md` · `PACK-16B-KEY-CUSTODY-REQUIREMENTS.md` | §4 | Stated as a rule with a rejection outcome, not a mitigation | **SATISFIED** | none | — |
| `AC-P16B-060` | Guardian lifecycle with all required states | round §14 | — | `PACK-16B-GUARDIAN-LIFECYCLE.md` | §2, §3 | 19 states with a transition table and per-state secret handling | **SATISFIED** | none | — |
| `AC-P16B-061` | Initial secrets destroyed at ceremony completion | round §14 | `[F-13]` | `PACK-16B-GUARDIAN-LIFECYCLE.md` · `PACK-16B-KEY-CUSTODY-REQUIREMENTS.md` | `GL-16`, §1 | Only `z_i` and `ẑ_i` survive the ceremony | **SATISFIED** | destruction is attested, not proved | `IM-16` |
| `AC-P16B-062` | Key reuse across contexts prohibited | round §12 | `[F-18]` | `PACK-16B-GUARDIAN-AND-QUORUM-MODEL.md` | `GQ-09` | The specification permits limited reuse; EPD² prohibits it | **SATISFIED** | none | — |
| `AC-P16B-063` | Guardian identity and organisation published | round §12 | — | `PACK-16B-GUARDIAN-AND-QUORUM-MODEL.md` | `GQ-06` | A secret guardian checks nobody | **SATISFIED** | personal exposure of volunteers | GOVERNANCE |
| `AC-P16B-064` | Guardian Organization defined as a role that holds nothing | round §28 | — | `PACK-16B-ROLE-SEPARATION-MATRIX.md` | `R-17`, `RS-16B-14` | Nominates, supports, is informed; may not direct its guardian | **SATISFIED** | none | — |
| `AC-P16B-065` | Twenty-phase key ceremony specified | round §15 | `[F-13]` | `PACK-16B-KEY-CEREMONY-SPECIFICATION.md` | §3 | All twenty phases with entry and exit conditions | **SATISFIED** | none | — |
| `AC-P16B-066` | Pre-publication commitment round added and justified | round §15 | `[F-15]`, `[F-16]` | `PACK-16B-KEY-CEREMONY-SPECIFICATION.md` | §4 | `KY-07`…`KY-12`; the countermeasure the specification already uses in decryption | **PARTIALLY SATISFIED** | a mitigation, not a fix; needs review | `TV-08` |
| `AC-P16B-067` | Canonical ceremony transcript specified | round §16 | — | `PACK-16B-CEREMONY-TRANSCRIPT-SPECIFICATION.md` | §2, §3 | A single canonical object with a defined hash chain | **SATISFIED** | none | — |
| `AC-P16B-068` | Complaint and disqualification protocol specified | round §17 | `[F-12]` | `PACK-16B-COMPLAINT-AND-DISQUALIFICATION-MODEL.md` | §2…§6 | 11 grounds, 7 publicly checkable; adjudication rules; three-attempt bound | **SATISFIED** | four grounds are assessed, not arithmetic | `OD-P16B-04` |
| `AC-P16B-069` | No administrator may mark a complaint resolved | round §17 | — | `PACK-16B-COMPLAINT-AND-DISQUALIFICATION-MODEL.md` | `CD-08` | Resolution requires arithmetic or an adjudication | **SATISFIED** | none | — |
| `AC-P16B-070` | Disqualification after joint-key formation forces a new context | round §17 | — | `PACK-16B-COMPLAINT-AND-DISQUALIFICATION-MODEL.md` | §6.1 | No retrofit of a formed key | **SATISFIED** | costly and correct | — |
| `AC-P16B-071` | Repeated ceremony failure has a bounded escalation | round §33 | — | `PACK-16B-COMPLAINT-AND-DISQUALIFICATION-MODEL.md` · `PACK-16B-FAILURE-AND-ABORT-MATRIX.md` | `CD-33`, `FM-16B-27` | Third failure discards the context; three named governance choices | **SATISFIED** | none | — |
| `AC-P16B-072` | Permitted custody classes defined; unacceptable ones refused | round §18 | — | `PACK-16B-KEY-CUSTODY-REQUIREMENTS.md` | §2 | Cloud KMS and consumer hardware wallets refused, with reasons | **SATISFIED** | weakest class bounds the profile | PACK-16D |
| `AC-P16B-073` | Custody requirements common to every class | round §18 | — | `PACK-16B-KEY-CUSTODY-REQUIREMENTS.md` | §3 | `KU-04`…`KU-16`, including no virtualisation and no shared provisioning | **SATISFIED** | attestation availability varies | PACK-16D |
| `AC-P16B-074` | Backup model selected that does not reduce the threshold | round §19 | — | `PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md` | §3 | Per-guardian, guardian-custodied, own share only | **SATISFIED** | stated and not minimised in §7 | — |
| `AC-P16B-075` | Escrow, split custody and central backup prohibited | round §19 | — | `PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md` | §4 | Nine prohibitions; a proposal is a design-review rejection | **SATISFIED** | none | — |
| `AC-P16B-076` | Compensated decryption treated explicitly | round §20 | `[F-11]` | `PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md` | §5 | **Does not exist in the pinned version.** No compensation material is created, stored or permitted | **NOT APPLICABLE** | none — its absence removes a drift surface | — |
| `AC-P16B-077` | Absence tolerance stated exactly | round §20 | `[F-11]` | `PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md` | `BR-14` | Exactly `n − k`: 2 default, 3 high assurance | **SATISFIED** | none | — |
| `AC-P16B-078` | Lost-guardian and quorum-loss model with bounded outcomes | round §21 | `[F-11]` | `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` | §5 | Pre-activation discard, post-closure annul; nothing else | **SATISFIED** | the result is genuinely unobtainable | — |
| `AC-P16B-079` | Compromise model with bounded governance outcomes | round §22 | — | `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` | §3, §4 | Nine classes; outcome determined by activation state, not preference | **SATISFIED** | none | — |
| `AC-P16B-080` | Secrecy and integrity claims never collapsed into one | round §22 | `[F-17]` | `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` | §2 | Stated separately throughout | **SATISFIED** | none | — |
| `AC-P16B-081` | No break-glass decryption | round §23 | — | `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` | §6 | No path exists; a proposal is `FM-16B-21` | **SATISFIED** | none | — |
| `AC-P16B-082` | No hidden master key | round §19 | — | `PACK-16B-BACKUP-RECOVERY-AND-COMPENSATION.md` · `PACK-16B-FAILURE-AND-ABORT-MATRIX.md` | `BR-09`…`BR-12`, `FM-16B-22` | Detection blocks activation or annuls; a published finding either way | **SATISFIED** | none | — |
| `AC-P16B-083` | Pre-closure decryption prohibited | round §24 | `[F-11]` | `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` | §7 | No operation exists before `voting_closed`; the attempt aborts and annuls | **SATISFIED** | none | — |
| `AC-P16B-084` | No intermediate tally in the ceremony domain | `FIR-INV-005` | — | `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` · `PACK-16B-REASON-CODE-SPECIFICATION.md` | `CM-20`, `RN-C12` | No `decryption.*` code carries a count, margin or aggregate | **SATISFIED** | none | — |
| `AC-P16B-085` | Readiness checks permitted without production ciphertext | round §24 | — | `PACK-16B-COMPROMISE-AND-QUORUM-LOSS-MODEL.md` | §7.1 | Test keys and synthetic ciphertexts only | **SATISFIED** | none | — |
| `AC-P16B-086` | Test and rehearsal key separation | round §25 | — | `PACK-16B-KEY-CEREMONY-SPECIFICATION.md` · `PACK-16B-FAILURE-AND-ABORT-MATRIX.md` | `KY-28`…`KY-33`, `FM-16B-24` | Six domains; a rehearsal transcript can never activate a real election | **SATISFIED** | demonstration needs a build | PACK-16D |
| `AC-P16B-087` | Remote versus in-person ceremony decided explicitly | round §29 | `[F-31]`, `[E-46]` | `PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md` | §1, §4 | Fully remote PROHIBITED; controlled hybrid permitted and expected | **SATISFIED** | logistics burden | `OD-P16B-05` |
| `AC-P16B-088` | Mandatory controls for the permitted hybrid form | round §29 | — | `PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md` | §6 | `RC-01`…`RC-14`; no guardian is alone with their device | **SATISFIED** | observer independence is assessed | GOVERNANCE |
| `AC-P16B-089` | What would change the remote decision is written down | round §29 | — | `PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md` | §5 | Four conditions, carried as an open decision | **SATISFIED** | none | `OD-P16B-05` |
| `AC-P16B-090` | The decryption ceremony is held no looser than the key ceremony | round §29 | — | `PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md` | §8, `RC-15` | Closes the obvious scheduling drift | **SATISFIED** | none | — |
| `AC-P16B-091` | Ceremony accessibility requirements | round §30 | — | `PACK-16B-KEY-CEREMONY-SPECIFICATION.md` · `PACK-16B-REMOTE-CEREMONY-ASSESSMENT.md` | `KY-34`…`KY-43`, §7 | Venue accessibility is a selection criterion; interpretation arranged in advance | **SATISFIED** | a set that cannot be assembled accessibly has not been assembled | GOVERNANCE |
| `AC-P16B-092` | An accessibility assistant gains no guardian capability | round §30 | — | `PACK-16B-KEY-CEREMONY-SPECIFICATION.md` | `KY-39`…`KY-41` | Assistance never touches secret material; dual control where it approaches | **SATISFIED** | none | — |
| `AC-P16B-093` | Twelve ceremony roles with a RACI | round §28 | — | `PACK-16B-ROLE-SEPARATION-MATRIX.md` | §1, §2 | 20-phase RACI; two new roles `R-17`, `R-18` | **SATISFIED** | none | — |
| `AC-P16B-094` | Non-combinable role matrix | round §28 | — | `PACK-16B-ROLE-SEPARATION-MATRIX.md` | §4 | Three PACK-16A cells tightened; new cells for `R-17`, `R-18` | **SATISFIED** | small organisations must recruit outward | `RS-16B-18` |
| `AC-P16B-095` | All eleven listed role prohibitions stated normatively | round §28 | — | `PACK-16B-ROLE-SEPARATION-MATRIX.md` | §3 | `RS-16B-03`…`RS-16B-13`, with an enforcement point each | **SATISFIED** | none | — |
| `AC-P16B-096` | Small-organisation case answered without merging roles | round §28 | — | `PACK-16B-ROLE-SEPARATION-MATRIX.md` | §7 | Recruit outward, or do not hold the vote electronically | **SATISFIED** | a real constraint on small units | GOVERNANCE |
| `AC-P16B-097` | Nineteen incident events with notification classes | round §31 | — | `PACK-16B-INCIDENT-AND-NOTIFICATION-MODEL.md` | §1 | Public, auditor, out-of-band, code, actor and timing bound for each | **SATISFIED** | none | — |
| `AC-P16B-098` | Suspicion is published while protecting a possibly innocent person | round §31 | — | `PACK-16B-INCIDENT-AND-NOTIFICATION-MODEL.md` | §3.1 | Existence and class always published; evidence may be withheld under `IN-23` | **PARTIALLY SATISFIED** | reputational cost to a volunteer | GOVERNANCE |
| `AC-P16B-099` | Timing precision separated between ceremony and participant domains | round §31 | — | `PACK-16B-INCIDENT-AND-NOTIFICATION-MODEL.md` | §5 | Exact for ceremony events; PACK-15 coarsening wherever a participant could be referenced | **SATISFIED** | none | — |
| `AC-P16B-100` | Immutable incident evidence | round §31 | — | `PACK-16B-INCIDENT-AND-NOTIFICATION-MODEL.md` | §6 | Append-only; corrections are new entries; destruction dates published in advance | **SATISFIED** | retention period is not chosen here | `OD-P16A-07` |
| `AC-P16B-101` | Twenty reason-code namespaces defined | round §32 | — | `PACK-16B-REASON-CODE-SPECIFICATION.md` | §2…§13 | 20 required namespaces plus 2 declared additions | **SATISFIED** | none | PACK-16D registry |
| `AC-P16B-102` | Reason codes are privacy-safe and non-secret-bearing | round §32 | — | `PACK-16B-REASON-CODE-SPECIFICATION.md` | §1, `RN-C05` | A closed field vocabulary; `guardian_index` permitted, `guardian_name` not | **SATISFIED** | none | — |
| `AC-P16B-103` | No generic catch-all reason code | round §32 | — | `PACK-16B-REASON-CODE-SPECIFICATION.md` | `RN-C04` | Two failures differing in consequence are two codes | **SATISFIED** | none | — |
| `AC-P16B-104` | Reason codes registered through the Canonical Schema Registry later | round §32 | — | `PACK-16B-REASON-CODE-SPECIFICATION.md` | `RN-C16` | Specification only; no registry implemented | **DEFERRED** | none | PACK-16D |
| `AC-P16B-105` | Twenty-six failure conditions with fixed outcomes | round §33 | — | `PACK-16B-FAILURE-AND-ABORT-MATRIX.md` | §1…§8 | 26 of 26 covered; 9 EPD²-added | **SATISFIED** | none | — |
| `AC-P16B-106` | No condition resolves to “governance decides” | round §33 | — | `PACK-16B-FAILURE-AND-ABORT-MATRIX.md` | `FM-16B-00`, §10 | Three conditions have bounded choices; eight named outcomes total | **SATISFIED** | none | — |
| `AC-P16B-107` | Mandatory implementation evaluation criteria for OD-P16A-04 | round §26 | — | `PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md` | §2…§9 | `IM-04`…`IM-38` mandatory; `IM-39`…`IM-45` weighted; performance non-decisive | **SATISFIED** | `RR-01` — no implementation exists | `OD-P16A-04` |
| `AC-P16B-108` | Side-channel, zeroization and secret-containment requirements | round §26 | — | `PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md` | §3, §4, §5 | Constant-time, zeroisation, no secret in logs, dumps, telemetry, exceptions or browser storage | **SATISFIED** | a browser cannot offer constant time — stated | PACK-16D |
| `AC-P16B-109` | Browser versus native/WASM split decided | round §26 | — | `PACK-16B-IMPLEMENTATION-EVALUATION-CRITERIA.md` | §6 | No guardian secret ever exists in a browser context; the verifier must exist outside a browser | **SATISFIED** | client compromise is detected, not prevented | PACK-16C |
| `AC-P16B-110` | Test-vector obligations defined | round §27 | — | `PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` | §1, §2 | `TV-01`…`TV-08`; 14 vector classes including unreachability vectors | **SATISFIED** | none | PACK-16D |
| `AC-P16B-111` | What requires proof, symbolic analysis, differential and expert review | round §27 | — | `PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` | §3 | A property-by-method mapping with the load-bearing method marked | **SATISFIED** | none | — |
| `AC-P16B-112` | OD-P16A-06 not falsely closed | round §27 | `[F-31]` | `PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` | §0, §4 | Named deliverable, named gate, status `blocked pending cryptographic review` | **BLOCKED** | `RR-09` — no analysis **located**; absence of evidence, not proof of absence | `TV-08`, external |
| `AC-P16B-113` | Upstream gaps not described as closed by an EPD² document | round §27 | `[F-30]`, `[F-31]` | `PACK-16B-TEST-VECTOR-AND-FORMAL-REVIEW-REQUIREMENTS.md` | §5, `TV-13` | Five gaps listed with EPD²’s only available response | **SATISFIED** | none | — |
| `AC-P16B-114` | Canon assessment performed without changing Canon | round §34 | — | `PACK-16B-CANON-ASSESSMENT.md` | §0, §6 | `CANON CLARIFICATION REQUIRED`; `CANON_VERSION` unchanged | **SATISFIED** | none | — |
| `AC-P16B-115` | Ceremony transcript assessed against PublicLedgerEntry | round §34 | — | `PACK-16B-CANON-ASSESSMENT.md` | `CQ-P16B-02` | Not a `PublicLedgerEntry`; the trust model differs | **SATISFIED** | none | PACK-16C |
| `AC-P16B-116` | PublicLedgerEntry → VoteEnvelope prohibition preserved | round §34 | — | `PACK-16B-CANON-ASSESSMENT.md` | §3.1 | Untouched and reinforced from the ceremony side | **SATISFIED** | none | — |
| `AC-P16B-117` | Amendment candidates recorded rather than proposed | round §34 | — | `PACK-16B-CANON-ASSESSMENT.md` | §5 | `CAM-P16B-01`…`03`; PACK-16A `CA-02` narrowed, not discharged | **SATISFIED** | none | PACK-16C, PACK-17 |
| `AC-P16B-118` | FIR coverage without false closure | round §35 | — | `PACK-16B-FIR-COVERAGE-MATRIX.md` | §1…§7 | 0 marked implemented; 0 created; 0 statuses changed | **SATISFIED** | `FIR-INV-002` cannot be closed by this round | PACK-16C+ |
| `AC-P16B-119` | Required FIR entries preserved | round §35 | — | `PACK-16B-FIR-COVERAGE-MATRIX.md` | §5 | All 11 named entries verified present and unmodified | **SATISFIED** | none | — |
| `AC-P16B-120` | OD-P15-05 closed or formally reassigned | round §4 | — | `PACK-16B-OPEN-DECISIONS.md` | §1 | Cryptographic boundary closed (`IS-01`…`IS-06`); construction reassigned to PACK-16C | **SATISFIED** | none | PACK-16C |
| `AC-P16B-121` | OD-P16A-03 closed or formally reassigned | round §4 | `[F-20]`…`[F-25]`, `[F-33]`…`[F-36]` | `PACK-16B-OPEN-DECISIONS.md` | §1, §3 | Closed for the dimensions assessed, including the current-edition subgroup-order dimension, with one divergence declared (Remark 2.12). General BSI compatibility of the whole profile is **not** closed | **SATISFIED** | `RB-09` — the Remark 2.12 divergence, blocking for production and legal activation | `VO-02`, `VO-03`; `VO-08` → external cryptographic review + PACK-17 |
| `AC-P16B-122` | OD-P16A-05 closed or formally reassigned | round §4 | `[F-30]` | `PACK-16B-OPEN-DECISIONS.md` | §1 | Closed — a stewardship model that survives upstream abandonment | **SATISFIED** | depends on EPD² operating its own intake | GOVERNANCE |
| `AC-P16B-123` | Contributions to the six named open decisions | round §4 | — | `PACK-16B-OPEN-DECISIONS.md` | §2 | Each contribution stated with what remains and who owns it | **SATISFIED** | four activation blocks remain open | various |
| `AC-P16B-124` | Repository and Canon versions unchanged | round §40 | — | **all** | — | `0.15.0` and `0.8.0` throughout | **SATISFIED** | none | — |
| `AC-P16B-125` | No source, test, migration, CI or lock change | round §40 | — | `PACK-16B-HANDOVER.md` | §5 | Verified by diff; counts published | **SATISFIED** | none | — |
| `AC-P16B-126` | One canonical evidence registry with all references resolving | round §38 | — | `PACK-16B-PROTOCOL-EVIDENCE-MATRIX.md` | §1, §4 | 32 entries, contiguous, 0 unresolved, 0 conflicting, 1 registry | **SATISFIED** | none | — |
| `AC-P16B-127` | Acceptance-matrix summary computed from rows | round §39 | — | `PACK-16B-ACCEPTANCE-MATRIX.md` | §3 | `sum(status counts) == requirement rows`, shown | **SATISFIED** | none | — |
| `AC-P16B-128` | No false implementation or certification claims | `FIR-INV-015` | — | **all** | headers, `RN-C09` | Every document carries the prohibition banner; no code may assert a prohibited claim | **SATISFIED** | none | — |
| `AC-P16B-129` | PACK-16C not started | round §44 | — | `PACK-16B-HANDOVER.md` | §0 | No PACK-16C artefact exists in this candidate | **SATISFIED** | none | — |

---

## 3. Summary — computed from the rows above

```text
Requirement rows                    129

SATISFIED                           116
PARTIALLY SATISFIED                   7
DEFERRED                              4
BLOCKED                               1
NOT APPLICABLE                        1
                                    ---
sum(status counts)                  129
```

**Process statuses are not acceptance statuses.** An earlier candidate
carried one row as `CORRECTED`; that row now carries the substantive status
the requirement reached (`SATISFIED`), with the correction recorded in its
decision cell. **`CORRECTED` appears nowhere as a status.**

### 3.1 The arithmetic check the round requires

```text
sum(status counts) == requirement rows
       129          ==       129          ✓

Distinct requirement IDs             129
Duplicate requirement IDs              0
Missing requirement IDs                0
Rows with no status                    0
Unsupported status values              0
Process statuses used as final         0
Rows with no decision document         0
Rows with no next stage                0
```

**Identifier range:** `AC-P16B-001` … `AC-P16B-129`, contiguous, no gaps.

---

## 4. The thirteen rows that are not `SATISFIED`, listed so they cannot hide

| ID              | Status                | What is actually open                                                                                     |
| --------------- | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| `AC-P16B-112`   | **`BLOCKED`**         | `OD-P16A-06` / `TV-08` — an external cryptographic review that has not been obtained                        |
| `AC-P16B-076`   | `NOT APPLICABLE`      | Compensated decryption — the mechanism does not exist in the pinned specification version                    |
| `AC-P16B-020`   | `PARTIALLY SATISFIED` | Test-key isolation is specified; **demonstration requires a build**                                          |
| `AC-P16B-027`   | `PARTIALLY SATISFIED` | The migration path is defined; **the successor profile does not exist** (`OD-P16B-06`)                       |
| `AC-P16B-042`   | `PARTIALLY SATISFIED` | The IND-CPA theorem applies as stated, and **has not been independently reviewed** `[F-31]`                  |
| `AC-P16B-044`   | `PARTIALLY SATISFIED` | No verifier-consumed field is changed — **EPD²'s own analysis**, pending `TV-11` and `TV-19`                 |
| `AC-P16B-048`   | `PARTIALLY SATISFIED` | The two specification inconsistencies are resolved **on EPD²'s reading**, unconfirmed by the authors          |
| `AC-P16B-066`   | `PARTIALLY SATISFIED` | The commitment round is **a mitigation of the GJKR exposure, not a fix**, and needs review                    |
| `AC-P16B-098`   | `PARTIALLY SATISFIED` | Publishing a suspicion has a **real cost to a possibly innocent volunteer**, mitigated and not removed        |
| `AC-P16B-023`   | `DEFERRED`            | Strong-Fiat–Shamir testing — no implementation exists to test                                                |
| `AC-P16B-024`   | `DEFERRED`            | Independent-verifier comparison — `TV-07`, `TV-19`                                                           |
| `AC-P16B-025`   | `DEFERRED`            | Implementation pinning and provenance — waits on `OD-P16A-04`                                                |
| `AC-P16B-104`   | `DEFERRED`            | Reason-code registration in the Canonical Schema Registry — PACK-16D                                         |

```text
1 BLOCKED + 7 PARTIALLY SATISFIED + 4 DEFERRED + 1 NOT APPLICABLE = 13
116 + 13 = 129   ✓
```

**`AC-P16B-112` is the one that matters and the one that cannot be fixed by
effort:** it is blocked on an external cryptographic review that has not
been obtained.

**`AC-P16B-021` moved to `SATISFIED` after direct first-hand review of the
locally supplied official BSI TR-02102-1 Version 2026-01 PDF.** The decision
no longer relies on reviewer attestation, search-result snippets or
secondary evidence: §2.3.3 p. 34 and §2.3.5 p. 36 are quoted verbatim in
`[F-36]`, and the comparison is `256 ≥ 250`. Its residual-risk cell carries
the one thing that remains — the Remark 2.12 published-parameter divergence,
`VO-08`, which **blocks production and legal activation** and is owned by
the PACK-16B external cryptographic review with independent confirmation in
PACK-17.

---

## 5. Coverage against the round task's required areas

| Required area                   | Anchor rows                                | Covered |
| ------------------------------- | ------------------------------------------ | ------- |
| All PACK-16A `KC` requirements  | `001`…`027` (`KC-01`…`KC-27`, one each)    | **27 of 27** |
| Parameter selection             | `028`…`037`                                | ✓       |
| BSI alignment                   | `021`, `022`, `038`…`040`                  | ✓       |
| ElectionGuard compatibility     | `041`…`044`                                | ✓       |
| Transcript safety               | `045`…`051`, `067`                         | ✓       |
| Randomness                      | `052`…`056`                                | ✓       |
| Guardian count                  | `003`, `057`                               | ✓       |
| Quorum                          | `001`, `004`, `057`                        | ✓       |
| Independence                    | `005`, `058`, `059`, `064`                 | ✓       |
| DKG                             | `007`…`009`, `065`, `066`                  | ✓       |
| Complaints                      | `068`…`071`                                | ✓       |
| Custody                         | `072`, `073`                               | ✓       |
| Backup                          | `014`, `074`, `075`                        | ✓       |
| Compensation                    | `011`, `076`, `077`                        | ✓       |
| Compromise                      | `012`, `079`, `080`                        | ✓       |
| Quorum loss                     | `013`, `078`                               | ✓       |
| No break-glass                  | `018`, `081`, `082`                        | ✓       |
| No intermediate tally           | `083`, `084`, `085`                        | ✓       |
| Remote ceremony                 | `087`…`092`                                | ✓       |
| Role separation                 | `016`, `093`…`096`                         | ✓       |
| Incident notification           | `017`, `097`…`100`                         | ✓       |
| Formal review                   | `110`…`113`                                | ✓       |
| Canon                           | `114`…`117`                                | ✓       |
| FIR                             | `118`, `119`                               | ✓       |

**24 of 24 required areas covered.** The anchors are indicative; several
areas are also touched by rows outside the ranges shown — reason codes
(`101`…`103`), failure outcomes (`105`, `106`), implementation criteria
(`107`…`109`), open decisions (`120`…`123`) and the archive rules
(`124`…`129`) support more than one area each.

---

## 6. What this matrix does not do

```text
It does not certify. It does not verify. It does not test.
It records which decisions were made, where, on what evidence,
and what remains — including one row that this round cannot close
and did not.
```

**SPECIFIED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.**
