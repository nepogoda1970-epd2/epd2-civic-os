# PACK-16A — Threat Model

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

This model **continues** `PACK-15-THREAT-MODEL.md`; it does not replace it.
PACK-15's thirty-nine threats `T-P15-01` … `T-P15-39` remain in force
unchanged, and where a PACK-16A threat extends one it says so. Forty-two
threats are recorded here, `T-P16A-01` … `T-P16A-42`.

Each entry states: **asset · attacker · precondition · attack path ·
affected invariant · preventive control · detective control · public
evidence · audit evidence · residual risk · failure behaviour · recovery
boundary · owning future stage**. Because thirteen columns do not fit one
table, each section carries **table A** (what the attack is) and **table
B** (what is done about it) keyed by the same identifier.

Owning stages: `PACK-16B` · `PACK-16C` · `PACK-16D` · `PACK-17` ·
`LEGAL/GOVERNANCE`.

**The five threats a correct-looking implementation is most likely to still
fail:** `T-P16A-04` (redemption-to-casting timing), `T-P16A-14` (board
equivocation), `T-P16A-19` (trustee collusion), `T-P16A-27` (verification
UI as a coercion instrument) and `T-P16A-36` (parameter provenance).

---

## 1. Adversaries in scope

| Class                     | Adversary                                                                                                                                            |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Participants              | malicious voter · coerced voter · vote buyer                                                                                                         |
| Election administration   | malicious election administrator · malicious eligibility administrator · malicious credential issuer · malicious voting-system operator              |
| Evidence infrastructure   | malicious bulletin-board operator · malicious verification-client operator · malicious frontend operator                                             |
| Cryptographic authorities | malicious trustee · colluding trustees                                                                                                               |
| Client and device         | compromised voting client · compromised verification client · malware on voter device · compromised browser · browser-extension attacker             |
| Network                   | network attacker · traffic-analysis attacker                                                                                                         |
| Privileged insiders       | database administrator · system administrator · security administrator · backup administrator · log administrator · insider with cross-system access |
| Supply chain              | supply-chain attacker · dependency-maintainer compromise · build-pipeline attacker                                                                   |
| Availability              | denial-of-service attacker                                                                                                                           |
| Cryptographic             | cryptographic-implementation attacker · future cryptanalytic attacker                                                                                |

**Explicitly assumed capable, not assumed absent:** every privileged
insider above is assumed to act, and every control below is written for a
world in which they do. PACK-15 ADR-090's rule stands: an incident that
genuinely requires cross-boundary read access is a context-level event
decided by governance, not resolved by a temporary grant.

---

## 2. Identity-to-ballot correlation

### 2.A

| #           | Threat                                                     | Asset         | Attacker                                 | Precondition                                                   | Attack path                                                                                     | Invariant                                |
| ----------- | ---------------------------------------------------------- | ------------- | ---------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `T-P16A-01` | **Continuation reference becomes the ballot ID**           | `FIR-INV-002` | Engineering convenience, not an attacker | A developer needs an idempotency key for casting               | Casting reuses the continuation reference as `BallotId` or derives one from it                  | `NO CONTINUATION REFERENCE AS BALLOT ID` |
| `T-P16A-02` | **Credential ID reused on the voting side**                | `FIR-INV-002` | Same                                     | The credential identifier is in scope at casting time          | The identifier is logged, echoed in an error, or stored beside the ballot                       | `NO CREDENTIAL ID AS BALLOT ID`          |
| `T-P16A-03` | **Reconciliation job recreates the redemption→ballot map** | Unlinkability | Voting-system operator                   | An operational need to explain a count discrepancy             | A job reads redemption records and board entries and pairs them by time or sequence             | PACK-15 §3 structural rule               |
| `T-P16A-04` | **Redemption-to-casting timing correlation**               | Unlinkability | Traffic-analysis attacker; DB admin      | Low-volume context; uncoarsened timestamps anywhere            | Redemption at t and board entry at t+δ in a quiet interval are plausibly the same participation | `NO PERSON-TO-BALLOT LINK`               |
| `T-P16A-05` | **Order-of-arrival correlation**                           | Unlinkability | Board operator; insider                  | The board publishes or retains true arrival order              | The n-th redemption is paired with the n-th board entry                                         | Same                                     |
| `T-P16A-06` | **Network source correlation between WS-03 and the board** | Unlinkability | Network attacker; hosting operator       | Both sides observable from one vantage point                   | Source addresses observed at redemption and at submission are matched                           | Same                                     |
| `T-P16A-07` | **Browser fingerprint correlation across origins**         | Unlinkability | Frontend operator; extension attacker    | Any fingerprinting surface in WS-03 or the verification origin | The same device signature appears at handoff and at casting                                     | `NO FINGERPRINTING`                      |
| `T-P16A-08` | **Verification-timing correlation**                        | Unlinkability | Board operator                           | The board records who fetched which entry, and when            | A verification lookup shortly after a submission identifies the submitter's entry               | `NO PERSON-TO-BALLOT LINK`               |
| `T-P16A-09` | **Cross-election linkage**                                 | Unlinkability | Insider with two contexts' data          | Any value stable across contexts                               | The same tracker, code, key or device signature appears in two elections                        | `NO GLOBAL USER ID`                      |
| `T-P16A-10` | **Backup or restore recreating the join**                  | Unlinkability | Backup administrator                     | Any shared restore target                                      | Two side-specific backups restored into one environment                                         | PACK-15 §3; ADR-090 §7                   |

### 2.B

| #           | Preventive control                                                                                                                                                      | Detective control                          | Public evidence           | Audit evidence         | Residual risk                                                                            | Failure behaviour                 | Recovery boundary                            | Owner                |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------- | ---------------------- | ---------------------------------------------------------------------------------------- | --------------------------------- | -------------------------------------------- | -------------------- |
| `T-P16A-01` | `BM-01`, `BM-02` — `BallotId` generated client-side from client randomness; no operation accepts a continuation reference at casting                                    | Structural test: no derivation path exists | —                         | Integrity stream       | A future "helpful" idempotency requirement will ask again; the refusal must be re-argued | fail closed                       | none — the linkage is not recoverable-from   | PACK-16D             |
| `T-P16A-02` | §3.2 prohibited-content list; error reporting by reason code only                                                                                                       | Prohibited-key scan over every payload     | —                         | Integrity stream       | An opaque re-derivation is not name-detectable                                           | fail closed                       | none                                         | PACK-16D             |
| `T-P16A-03` | No principal reads both stores; prohibited-construction list; `BM-04`                                                                                                   | Principal inventory per store              | —                         | `AS-04` lineage        | The need is legitimate and recurring; process, not code, is the weak point               | refuse                            | context-level only                           | PACK-16D, PACK-12    |
| `T-P16A-04` | Coarsened timestamps at `timestamp_granularity`; **submission batching and randomized publication delay** (`BB-11`); minting delay (PACK-15 §19.3)                      | Issuance- and submission-rate monitoring   | Board publication cadence | Integrity stream       | **Real in low-volume contexts. Reduced, bounded, not eliminated** — extends `T-P15-13`   | continue with recorded risk event | none                                         | **PACK-16C**         |
| `T-P16A-05` | Canonical board order is **board sequence after batching**, not arrival; no arrival timestamp finer than granularity (`BM-06`, `BB-11`)                                 | Board ordering review                      | Published ordering rule   | Board checkpoint chain | A single-ballot batch reveals order; §7 small-electorate policy applies                  | continue with recorded risk event | none                                         | PACK-16C             |
| `T-P16A-06` | Separate origins; guidance on independent access; no shared infrastructure                                                                                              | —                                          | —                         | —                      | **Not solvable at the application layer**; extends `T-P15-10`                            | n/a                               | n/a                                          | **PACK-17**          |
| `T-P16A-07` | No analytics, no third-party script origin, no fingerprinting surface, CSP with no third-party origin (ADR-096)                                                         | CSP violation reports                      | Published CSP             | `AS-06`                | An extension in the voter's browser is outside every control                             | fail closed on CSP violation      | none                                         | FRONT-PACK, PACK-16C |
| `T-P16A-08` | Board reads are **unauthenticated, unlogged at per-entry granularity**, and the full board is downloadable so a lookup is indistinguishable from a bulk fetch (`BB-09`) | Access-pattern review at aggregate level   | Board access policy       | `AS-06`                | A mirror operator can still observe fetches                                              | continue                          | none                                         | PACK-16C             |
| `T-P16A-09` | Per-context keys, per-context codes, no cross-context derivation; PACK-15 §10.3 pseudonym rules unchanged                                                               | Cross-context derivability test            | —                         | Integrity stream       | A leaked derivation secret retroactively links one context                               | fail closed                       | destruction of secrets at retention boundary | PACK-16D             |
| `T-P16A-10` | Separate backup domains and restore targets; restore into a shared environment is prohibited by policy and by topology                                                  | Backup topology review                     | —                         | `AS-06`                | A restore under incident pressure is the classic breach                                  | refuse restore                    | governance-declared incident                 | **PACK-17**          |

---

## 3. Ballot integrity

### 3.A

| #           | Threat                                                     | Asset                   | Attacker                           | Precondition                                     | Attack path                                                                           | Invariant                                  |
| ----------- | ---------------------------------------------------------- | ----------------------- | ---------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------- | ------------------------------------------ |
| `T-P16A-11` | **Ballot substitution**                                    | Outcome                 | Board operator; system admin       | Write access to the board store                  | An accepted entry is replaced with a different ciphertext                             | `NO SILENT BALLOT REPLACEMENT`             |
| `T-P16A-12` | **Ballot deletion**                                        | Outcome; franchise      | Board operator; system admin       | Same                                             | An accepted entry is removed before the closure checkpoint                            | `NO SILENT BALLOT DELETION`                |
| `T-P16A-13` | **Selective publication**                                  | Outcome                 | Board operator                     | The board controls what each reader sees         | Some accepted ballots are withheld from the public view but counted, or vice versa    | `APPEND-ONLY VERIFIABLE ELECTION EVIDENCE` |
| `T-P16A-14` | **Bulletin-board equivocation / split view**               | Universal verifiability | Board operator                     | No independent mirrors; no signed checkpoints    | Different readers are served different boards; each verifies successfully             | Same                                       |
| `T-P16A-15` | **Late insertion after closure**                           | Outcome                 | Board operator; admin              | Closure is not cryptographically fixed           | A ballot is added after the closure checkpoint and included in the aggregate          | Same                                       |
| `T-P16A-16` | **Duplicate casting / ballot stuffing**                    | Outcome                 | Malicious voter; credential issuer | Continuation capability re-obtainable            | The same authorisation yields two accepted ballots                                    | `CC-01`                                    |
| `T-P16A-17` | **Replay of another voter's ballot** (ballot independence) | Ballot secrecy          | Malicious voter                    | Ciphertexts admitted without plaintext knowledge | A target's ciphertext is copied and resubmitted; the result reveals the target's vote | Ballot secrecy                             |
| `T-P16A-18` | **Malicious ballot construction / invalid proof accepted** | Outcome                 | Malicious voter; weak verifier     | Proof verification is incomplete or weak         | A ballot encoding an out-of-range value is accepted and inflates a total              | Outcome integrity                          |

### 3.B

| #           | Preventive control                                                                                                   | Detective control                                     | Public evidence                    | Audit evidence          | Residual risk                                                                                 | Failure behaviour         | Recovery boundary           | Owner                       |
| ----------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------- | ----------------------- | --------------------------------------------------------------------------------------------- | ------------------------- | --------------------------- | --------------------------- |
| `T-P16A-11` | Append-only semantics; signed checkpoints; independent mirrors; `BM-05`                                              | Checkpoint chain verification by mirrors and auditors | Checkpoint chain; mirror agreement | Board audit stream      | A substitution before the first checkpoint is only caught by the voter                        | **abort or annul**        | re-run the context          | PACK-16C                    |
| `T-P16A-12` | Same; plus per-voter confirmation-code lookup (`BM-18`)                                                              | Voter-reported absence (`BM-19`); mirror comparison   | Same                               | Same                    | A deletion the voter never checks is undetected — take-up is 9.9 % at best `[E-29]`           | **abort or annul**        | re-run                      | PACK-16C                    |
| `T-P16A-13` | One canonical election-scoped namespace; the whole board is published, not queried per reader (`BB-09`)              | Mirror comparison; full-board hash                    | Full board download; board hash    | Board audit stream      | An auditor who checks only their own view sees nothing wrong                                  | abort                     | re-run                      | PACK-16C                    |
| `T-P16A-14` | **Signed checkpoints with a hash chain, published to ≥ 2 independent mirrors under distinct organisational control** | Mirror divergence detection; auditor cross-check      | Checkpoints on every mirror        | Board audit stream      | Mirrors under one operator are not independent; independence is organisational, not technical | **abort — uncertifiable** | governance: annul or re-run | **PACK-16C**                |
| `T-P16A-15` | Closure is a signed checkpoint fixing the ballot set (`BM-20`); the aggregate is computed over that set only         | Checkpoint timestamp and chain verification           | Closure checkpoint                 | Board audit stream      | Clock manipulation shifts the boundary; see `T-P16A-38`                                       | abort                     | re-run                      | PACK-16C                    |
| `T-P16A-16` | `CC-01` exactly-once consumption; `CC-08` no automatic re-issue; board rejects duplicate `BallotId` (`BM-05`)        | Aggregate reconciliation: ballots ≤ authorisations    | Published counts after closure     | Credential audit stream | A compromised credential issuer can mint authorisations; separation of duties is the control  | fail closed               | governance                  | PACK-16D                    |
| `T-P16A-17` | **`BM-14` — proof of knowledge of the plaintext is required on submission**; duplicate ciphertexts rejected          | Duplicate-ciphertext scan at acceptance               | Published proofs                   | Board audit stream      | None known for this construction; the risk is an implementation that skips the check          | reject ballot             | none needed                 | PACK-16D                    |
| `T-P16A-18` | `BM-15`, `BM-16` — range and contest-sum proofs verified **before acceptance**, never repaired                       | Independent verifier re-checks every proof            | Published proofs                   | Board audit stream      | **Weak Fiat–Shamir in an implementation defeats this silently** (`F-INF-2`)                   | reject ballot             | none                        | **PACK-16D**, `AC-P16A-039` |

---

## 4. Tally and trustee threats

### 4.A

| #           | Threat                                              | Asset                   | Attacker                     | Precondition                             | Attack path                                                                 | Invariant                    |
| ----------- | --------------------------------------------------- | ----------------------- | ---------------------------- | ---------------------------------------- | --------------------------------------------------------------------------- | ---------------------------- |
| `T-P16A-19` | **Trustee collusion**                               | Ballot secrecy          | Colluding trustees           | A quorum acts together                   | A quorum decrypts individual ballots rather than the aggregate              | Ballot secrecy               |
| `T-P16A-20` | **Early tally by a quorum before closure**          | `NO INTERMEDIATE TALLY` | Trustees + election officer  | Any pre-closure decryption path exists   | The quorum decrypts the running aggregate                                   | `NO INTERMEDIATE TALLY`      |
| `T-P16A-21` | **Partial-decryption leakage**                      | Outcome confidentiality | Malicious trustee            | Shares are published before combination  | A published share plus the ciphertext leaks information about the aggregate | Same                         |
| `T-P16A-22` | **Single-admin decryption via key concentration**   | Ballot secrecy          | System admin; security admin | One principal accumulates enough shares  | Shares are stored where one role can read them                              | `NO SINGLE-ADMIN DECRYPTION` |
| `T-P16A-23` | **Trustee unavailability blocking the tally**       | Availability; franchise | Denial-of-service; attrition | Quorum not met                           | Enough trustees are unreachable that the result cannot be produced          | Availability                 |
| `T-P16A-24` | **Recovery mechanism creating a hidden master key** | Ballot secrecy          | Well-intentioned operator    | A "lost trustee" recovery is designed in | An escrow reconstructs the private key outside the ceremony                 | `NO SINGLE-ADMIN DECRYPTION` |

### 4.B

| #           | Preventive control                                                                                                                              | Detective control                              | Public evidence                             | Audit evidence        | Residual risk                                                                      | Failure behaviour                   | Recovery boundary                     | Owner             |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------------------- | --------------------- | ---------------------------------------------------------------------------------- | ----------------------------------- | ------------------------------------- | ----------------- |
| `T-P16A-19` | Quorum drawn from **independent organisations**, not roles in one body; dual control; ceremony evidence                                         | Ceremony evidence; decryption-share proofs     | Trustee list; ceremony record; share proofs | Ceremony audit stream | **A quorum that colludes defeats the construction. This is a property, not a bug** | detect after the fact only          | governance: annul; cannot un-disclose | **PACK-16B**      |
| `T-P16A-20` | `BM-21` — decryption bound to `voting_closed`; no pre-closure operation exists                                                                  | Ceremony evidence timestamps                   | Ceremony record                             | Ceremony audit stream | A trustee holding a share can compute offline against a copied ciphertext set      | **abort**                           | annul                                 | PACK-16B          |
| `T-P16A-21` | Shares are produced and combined **within the closure ceremony**; no share is published before the combined result                              | Share-proof verification                       | Shares published **with** the result        | Ceremony audit stream | —                                                                                  | abort                               | annul                                 | PACK-16B          |
| `T-P16A-22` | Separation of Security Admin and System Admin (`FIR-INV-008`); no role may hold a quorum; custody is per-trustee                                | Custody inventory; privileged-session evidence | Trustee custody statement                   | `AS-06`               | Physical custody is an organisational control, not a technical one                 | refuse ceremony                     | governance                            | PACK-16B, PACK-12 |
| `T-P16A-23` | Quorum k strictly less than n; compensated shares for missing trustees `[E-04]`; availability planning                                          | Pre-ceremony readiness check                   | Quorum policy                               | Ceremony audit stream | Quorum loss makes a result unobtainable — see `FM-P16A-12`                         | **pause, then abort if unresolved** | re-run only; **never a key escrow**   | PACK-16B          |
| `T-P16A-24` | **No escrow. No master key. No break-glass decryption path.** A recovery that reconstructs the key outside the ceremony is prohibited by design | Design review; ceremony record                 | Published statement that no escrow exists   | Ceremony audit stream | Losing a quorum means losing the result; that cost is accepted deliberately        | refuse                              | re-run                                | **PACK-16B**      |

`T-P16A-24` is the trade this architecture makes explicitly: **an
unrecoverable election is preferable to a recoverable secret.** PACK-15
made the identical trade for credential delivery (§13.2) and this round
keeps it.

---

## 5. Coercion, receipts and vote buying

### 5.A

| #           | Threat                                                     | Asset                | Attacker                   | Precondition                                     | Attack path                                                                               | Invariant                        |
| ----------- | ---------------------------------------------------------- | -------------------- | -------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------- | -------------------------------- |
| `T-P16A-25` | **Receipt misuse as proof of choice**                      | Free suffrage        | Vote buyer; coercer        | A receipt reveals or commits to the choice       | The coercer demands the receipt and verifies the choice                                   | `NO RECEIPT THAT REVEALS CHOICE` |
| `T-P16A-26` | **Screen-sharing / shoulder coercion during casting**      | Free suffrage        | Coercer; household member  | Remote, uncontrolled environment                 | The coercer observes the casting act directly                                             | Free suffrage                    |
| `T-P16A-27` | **Verification UI as a coercion instrument**               | Free suffrage        | Coercer                    | The verification client displays the choice      | The coercer compels a verification session and watches the plaintext appear               | Same                             |
| `T-P16A-28` | **Fake verification interface**                            | Trust; free suffrage | Frontend attacker; coercer | Verification origin is spoofable                 | A fake verifier shows what the coercer wants, or reassures a voter whose ballot is absent | Individual verifiability         |
| `T-P16A-29` | **Vote buying at scale via challenge transcripts**         | Free suffrage        | Vote buyer                 | A challenged ballot's opening is transferable    | A buyer requires the voter to challenge, prove a choice, then cast the same choice        | Receipt-freeness boundary        |
| `T-P16A-30` | **Forced abstention**                                      | Universal suffrage   | Coercer                    | The coercer can observe or prevent participation | The voter is prevented from casting at all                                                | Free suffrage                    |
| `T-P16A-31` | **Remote observation / remote desktop during the session** | Free suffrage        | Coercer; "helper"          | Screen sharing is possible                       | The whole session is observed from elsewhere                                              | Same                             |
| `T-P16A-32` | **Assistant becomes coercer in an assisted session**       | Free suffrage        | Helper                     | Assisted voting is offered                       | The helper sees or controls the choice                                                    | Same; `FIR-INCLUSION-001`        |

### 5.B

| #           | Preventive control                                                                                                                                                                 | Detective control                                   | Public evidence                  | Audit evidence     | Residual risk                                                                                       | Failure behaviour | Recovery boundary                  | Owner                  |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | -------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------- | ----------------- | ---------------------------------- | ---------------------- |
| `T-P16A-25` | `BM-03` — the confirmation code derives only from encryptions and reveals nothing about the choice `[E-05]`                                                                        | —                                                   | Published code construction      | —                  | The code proves **participation**, which is itself coercive information in some settings            | n/a               | none                               | PACK-16C               |
| `T-P16A-26` | **None available.** Remote casting cannot prevent observation `[E-46]`                                                                                                             | —                                                   | Published statement of the limit | —                  | **Unmitigated. Stated, not solved.** Governance may require an in-person channel instead            | n/a               | context-level: alternative channel | **LEGAL/GOVERNANCE**   |
| `T-P16A-27` | Verification shows **presence of the confirmation code on the board**, never the choice; no operation reveals a choice post-cast                                                   | —                                                   | Published verification semantics | —                  | A coercer present during **casting** already has the choice; verification adds nothing then         | n/a               | none                               | PACK-16C               |
| `T-P16A-28` | Separate verification origin under EPD² control; published board and mirror addresses; the board is independently downloadable                                                     | Mirror comparison by the voter or a third party     | Published mirror list            | `AS-06`            | A voter who uses only the interface handed to them is not protected                                 | fail visibly      | none                               | PACK-16C               |
| `T-P16A-29` | A challenged ballot is **spoiled and never tallied** (`BM-09`); proving a challenged choice proves nothing about the cast ballot                                                   | Challenge-rate monitoring after closure             | Spoiled ballots on the board     | Board audit stream | A buyer may still pay for compliance-shaped behaviour; the transcript is not proof of the cast vote | n/a               | none                               | PACK-16C               |
| `T-P16A-30` | **Not addressed by the selected profile.** Only coercion-resistant schemes address it, and none is selectable (§3.6 of the comparison)                                             | Participation-rate anomalies **after closure only** | —                                | Aggregate evidence | **Unmitigated. Stated.**                                                                            | n/a               | context-level                      | **LEGAL/GOVERNANCE**   |
| `T-P16A-31` | Prohibition on screen sharing during the voting session, stated in the interface and in governed content; no operator-visible surface                                              | —                                                   | Published guidance               | —                  | Unenforceable technically                                                                           | n/a               | none                               | FRONT-PACK, GOVERNANCE |
| `T-P16A-32` | PACK-15 §13.5 unchanged: assistance ends at the boundary; the accessible path is **independent, not supervised**; assisted-action receipts record the assistance, never the choice | Assisted-action receipts                            | —                                | `AS-06`            | An assisted voter in a coercive household is not protected by any technical control                 | n/a               | context-level                      | PACK-16C, GOVERNANCE   |

**`T-P16A-26` and `T-P16A-30` are recorded as unmitigated.** That is the
honest position and it is the same position taken by every system in the
comparison that addressed it at all `[E-14]`, `[E-17]`, `[E-46]`.

---

## 6. Client, device and supply chain

### 6.A

| #           | Threat                                                    | Asset                | Attacker                       | Precondition                            | Attack path                                                              | Invariant         |
| ----------- | --------------------------------------------------------- | -------------------- | ------------------------------ | --------------------------------------- | ------------------------------------------------------------------------ | ----------------- |
| `T-P16A-33` | **Compromised voting client encrypts a different choice** | Cast as intended     | Malware; malicious operator    | Client integrity not assured            | The client displays one selection and encrypts another                   | Cast as intended  |
| `T-P16A-34` | **Dishonest challenge handling**                          | Cast as intended     | Compromised client             | The client learns cast/challenge first  | The client behaves honestly only when challenged                         | Same              |
| `T-P16A-35` | **Weak randomness in the client**                         | Ballot secrecy       | Implementation attacker        | Poor entropy source                     | Encryption nonces become predictable; ballots become decryptable         | Ballot secrecy    |
| `T-P16A-36` | **Cryptographic parameter subversion**                    | Everything           | Supply-chain attacker; insider | Parameters generated without provenance | A trapdoor permits transcripts that verify while altering votes `[E-33]` | Outcome integrity |
| `T-P16A-37` | **Build-pipeline or dependency compromise**               | Everything           | Supply-chain attacker          | Unpinned or unverified dependencies     | A malicious build ships a client that leaks or alters                    | Everything        |
| `T-P16A-38` | **Clock inconsistency shifting the window**               | Franchise; integrity | Insider; misconfiguration      | Trusted local clocks                    | Ballots are accepted after closure or refused before it                  | Outcome integrity |
| `T-P16A-39` | **Cryptographic parameter downgrade**                     | Ballot secrecy       | Insider                        | Downgrade is warned, not refused        | A context is configured with weaker parameters                           | `BM-32`           |
| `T-P16A-40` | **Future cryptanalytic attacker**                         | Ballot secrecy       | Future adversary               | Published ciphertexts retained          | A future break decrypts an archived election's individual ballots        | Long-term secrecy |

### 6.B

| #           | Preventive control                                                                                                              | Detective control                      | Public evidence                     | Audit evidence        | Residual risk                                                                                                               | Failure behaviour          | Recovery boundary          | Owner                 |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | ----------------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------- | -------------------------- | -------------------------- | --------------------- |
| `T-P16A-33` | **Challenge/spoil is the mechanism** (`BM-07`…`BM-13`); client integrity evidence; subresource integrity; no third-party origin | Aggregate challenge outcomes           | Spoiled ballots on the board        | Board audit stream    | **Probabilistic and dependent on take-up; a low-rate cheater may go undetected.** No candidate system solves this           | detect; abort if confirmed | annul / re-run             | PACK-16C              |
| `T-P16A-34` | `BM-07` — commitment to the confirmation code **precedes** the cast/challenge choice                                            | Same                                   | Same                                | Same                  | A client that guesses the voter's intent statistically still gains an edge                                                  | detect                     | annul                      | PACK-16C              |
| `T-P16A-35` | Randomness requirements and self-test at ballot preparation; refuse to encrypt on failure                                       | Client self-test result reason code    | Published requirement               | `AS-06`               | Browser entropy quality is not directly observable                                                                          | **fail closed**            | none needed                | PACK-16C, PACK-16D    |
| `T-P16A-36` | **Published, independently reproducible parameter provenance with a proof of how parameters arose** (`BM-33`, `F-INF-3`)        | Independent reproduction by an auditor | Parameter provenance document       | Ceremony audit stream | A provenance nobody reproduces is a provenance nobody checked                                                               | refuse activation          | re-run with new parameters | **PACK-16B**          |
| `T-P16A-37` | Pinned, verified dependencies; reproducible builds; published artefact hashes; PACK-13 supply-chain discipline                  | Build attestation verification         | Published build hashes              | `AS-06`               | A maintainer compromise upstream is outside EPD²'s control                                                                  | **fail closed**            | re-run                     | PACK-16D, PACK-17     |
| `T-P16A-38` | Window boundaries fixed by **signed checkpoints**, not by local clocks; clock skew bounds declared                              | Checkpoint chain and skew monitoring   | Closure checkpoint                  | Board audit stream    | A skew inside the bound is undetectable                                                                                     | pause                      | extend or re-run           | PACK-16C              |
| `T-P16A-39` | `BM-32` — **downgrade is refused, not warned**; configuration outside range fails validation                                    | Configuration validation records       | Published parameter set identifier  | `AS-06`               | —                                                                                                                           | fail closed                | none                       | PACK-16B              |
| `T-P16A-40` | Cryptographic agility (`BM-30`…`BM-35`); retention limits on published ciphertexts balanced against audit obligations           | —                                      | Published parameter set and version | Archive evidence      | **A published encrypted ballot set is a long-term secrecy liability.** Retention vs. verifiability is an unresolved tension | n/a                        | none                       | `OD-P16A-07`, PACK-17 |

`T-P16A-40` is recorded as an **open tension** rather than as a solved
threat: universal verifiability wants the record kept forever, and ballot
secrecy wants it destroyed. `PACK-16A-OPEN-DECISIONS.md` `OD-P16A-07`
carries it, and no round may resolve it by quietly choosing one side.

---

## 7. Disclosure, disputes and governance

### 7.A

| #           | Threat                                                    | Asset          | Attacker                  | Precondition                                      | Attack path                                                                      | Invariant                                                  |
| ----------- | --------------------------------------------------------- | -------------- | ------------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `T-P16A-41` | **Small-group result disclosure**                         | Ballot secrecy | Any reader                | A published cell below the disclosure minimum     | A result for a body of six identifies how individuals voted, or nearly           | `FIR-INV-011`                                              |
| `T-P16A-42` | **Dispute process used to build a person-to-ballot link** | `FIR-INV-002`  | Well-intentioned reviewer | A participant asks for their ballot to be checked | A trustee quorum is asked to decrypt one ballot "with the participant's consent" | `NO INDIVIDUAL BALLOT CORRECTION THROUGH IDENTITY LINKAGE` |

### 7.B

| #           | Preventive control                                                                                                                                        | Detective control                            | Public evidence          | Audit evidence       | Residual risk                                                                                                                  | Failure behaviour    | Recovery boundary           | Owner                |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ------------------------ | -------------------- | ------------------------------------------------------------------------------------------------------------------------------ | -------------------- | --------------------------- | -------------------- |
| `T-P16A-41` | `disclosure_min_cell = 5` with **complementary suppression applied jointly across the whole published set** (scope §8); small-electorate policy unchanged | Disclosure-control review before publication | Suppression metadata     | `AS-05`              | **In a body of eleven, no control makes participation unlinkable to the eleven** — PACK-15 §19.4's honest statement, unchanged | suppress or withhold | governance                  | LEGAL/GOVERNANCE     |
| `T-P16A-42` | `ADR-098` unchanged; §9.1 of the ballot model — **no operation exists**, and consent does not create one; the request is refused as an act                | Dispute-record review                        | Published dispute policy | Dispute audit stream | The request will be made, sympathetically, and refusing it will be unpopular                                                   | **refuse**           | context-level remedies only | PACK-16C, GOVERNANCE |

---

## 8. Mapping to PACK-15

| PACK-15 threat | Extended by              | How                                                                     |
| -------------- | ------------------------ | ----------------------------------------------------------------------- |
| `T-P15-05`     | `T-P16A-01`, `T-P16A-02` | Credential correlation extended past redemption into the ballot         |
| `T-P15-10`     | `T-P16A-06`              | IP/device correlation extended to the board and verification origins    |
| `T-P15-12`     | `T-P16A-03`, `T-P16A-22` | Operator correlation extended to trustees and board operators           |
| `T-P15-13`     | `T-P16A-04`, `T-P16A-05` | Timing correlation extended across the casting boundary; batching added |
| `T-P15-18`     | `T-P16A-03`, `T-P16A-10` | Audit-stream joins extended to the board and ceremony streams           |
| `T-P15-27`     | `T-P16A-41`              | Small-group disclosure extended from participation to **results**       |
| `T-P15-37`     | `T-P16A-04`              | Queue side channel extended to submission batching                      |
| `T-P15-38`     | `T-P16A-33`, `T-P16A-35` | Material escaping WS-03 extended to ballot randomness and plaintext     |
| `T-P15-39`     | `T-P16A-41`              | Evidence-bundle differencing extended to published results              |

**No PACK-15 threat is closed by this round.**

---

## 9. What this threat model does not cover

| Not covered                                                         | Why                                                   | Owner                |
| ------------------------------------------------------------------- | ----------------------------------------------------- | -------------------- |
| Network and infrastructure metadata correlation                     | Outside the application boundary                      | **PACK-17**          |
| Denial of service, capacity and resilience                          | Availability architecture is not this round's subject | **PACK-17**          |
| Physical security of trustee custody                                | Ceremony design is not this round's subject           | **PACK-16B**         |
| Voter-device compromise beyond challenge/spoil                      | No candidate system addresses it `[E-17]`, `[E-28b]`  | out of scope; stated |
| Legal compulsion directed at participants rather than at the system | Not a technical control                               | **LEGAL/GOVERNANCE** |
| Social pressure inside a small body that knows its own membership   | Not addressable by any system                         | **LEGAL/GOVERNANCE** |

**SPECIFIED. ASSESSED. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY. NOT
LEGALLY ACTIVATED.**
