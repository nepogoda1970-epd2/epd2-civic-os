# PACK-15 — Threat Model

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Each row states the protected asset, the attacker or failure, the trust
boundary crossed, the preventive control, the detective control, the
evidence produced, the residual risk this round cannot close, and the pack
that owns the remainder.

**Thirty-nine threats.** The four that a correct-looking implementation is
most likely to still fail are `T-P15-12` (operator correlation),
`T-P15-13` (timing correlation), `T-P15-18` (audit-stream joins) and
`T-P15-27` (small-group disclosure).

---

## 1. Identifier leakage

| #          | Threat                                                                     | Asset                     | Attacker / failure                        | Boundary            | Preventive control                                                          | Detective control                | Evidence               | Residual risk                                                              | Dependency        |
| ---------- | -------------------------------------------------------------------------- | ------------------------- | ----------------------------------------- | ------------------- | --------------------------------------------------------------------------- | -------------------------------- | ---------------------- | -------------------------------------------------------------------------- | ----------------- |
| `T-P15-01` | **Global identifier leakage** — an identifier becomes universal            | `FIR-INV-001`             | Engineering convenience, not an attacker  | Every hop           | Assertion prohibited-content list; scoped actor references; ADR-091          | Prohibited-key and derivability scans | Scan records       | An opaque re-derivation is not name-detectable                             | Implementation    |
| `T-P15-02` | **Member-number leakage** into an assertion or credential                  | Member privacy            | Import, support tooling, "useful context" | `H-03`, `H-04`      | Structural absence; canon 10.1's forbidden-field set extended               | Payload scans                    | Scan records           | Member numbers remain quotable outside the system                          | —                 |
| `T-P15-03` | **Account ID leakage** across the boundary                                 | `FIR-INV-002`             | Trace propagation, error payloads         | `H-04`, `H-05`      | Explicit trace break; error reporting by reason code only                   | Boundary payload inspection      | Integrity stream       | A misconfigured SDK can re-enable propagation silently                     | Implementation    |
| `T-P15-04` | **Persistent pseudonym across contexts**                                   | Unlinkability             | A "stable anonymous ID" added for analytics | `H-04`            | Context-scoped derivation with a context-scoped secret; deletion at boundary | Cross-context derivability test  | Assertion audit        | A leaked derivation secret retroactively links one context                 | Implementation    |

## 2. Correlation

| #          | Threat                                                                         | Preventive control                                                                                | Detective control                       | Residual risk                                                                          | Dependency        |
| ---------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------- | ----------------- |
| `T-P15-05` | **Credential correlation** — credential linked to an assertion                  | **Set-not-map** spent-nonce store; no assertion reference in the credential record (ADR-093)      | Structural test: no store holds both    | None from stored data; timing remains                                                  | —                 |
| `T-P15-06` | **Assertion→credential mapping recreated by a reconciliation job**              | Prohibited construction list; no principal reads both stores                                      | Principal inventory per store           | A future operational need will ask for it; the refusal must be re-argued               | Implementation    |
| `T-P15-07` | **Shared idempotency or request key across the boundary**                       | Idempotency keyed on the nonce, voting side only; no key echoed back                              | Boundary payload inspection             | —                                                                                      | —                 |
| `T-P15-08` | **Backup or replica combining both sides**                                      | Backup topology is part of the boundary; separate backup domains                                   | Backup topology review                  | Restores into a shared environment recreate the join                                   | PACK-17           |
| `T-P15-09` | **Data warehouse ingesting both audit streams**                                 | Separate stream authorization; no unified sink                                                     | Sink inventory                          | An analytics platform is the least-reviewed place a join can appear                    | Implementation    |
| `T-P15-10` | **IP / device correlation** between WS-02 and WS-03                             | Separate origin; no shared client state; guidance on independent access                            | —                                       | **Network-layer correlation is not solvable at the application layer**                 | PACK-17           |
| `T-P15-11` | **Analytics correlation**                                                       | No analytics of any kind in WS-03; no third-party script; no session replay                       | CSP violation reports                   | —                                                                                      | FRONT-PACK        |
| `T-P15-12` | **Operator correlation** — one human watching both sides during a live vote     | `SD-06`; separate authorization; break-glass may not span sides; auditor notification             | Privileged session evidence             | A person with legitimate access to one side and physical proximity to the other        | PACK-12 + process |
| `T-P15-13` | **Timing correlation**                                                          | Coarsened timestamps; timing-class logs; batching and jitter; minimum-cohort policy (`OD-P15-02`) | Issuance-rate monitoring                | **Real in low-volume contexts. Reduced, not eliminated**                               | `OD-P15-02`, PACK-16 |
| `T-P15-14` | **Infrastructure metadata correlation**                                         | Outside the application boundary; named, not claimed solved                                       | —                                       | Owned by deployment and network design                                                 | PACK-17           |
| `T-P15-15` | **Log correlation** — the same value in two logs                                | No cross-boundary identifier is ever logged; nonces never logged in plaintext                     | Log field inventory                     | Debug logging enabled in an incident is the classic breach                             | Implementation    |

## 3. Replay, duplication and issuance integrity

| #          | Threat                                          | Preventive control                                                                     | Detective control                    | Residual risk                                                | Dependency |
| ---------- | ----------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------ | ---------- |
| `T-P15-16` | **Assertion replay**                            | One-time nonce; atomic spent-marking; expiry; audience and purpose binding             | `ASSERTION_ALREADY_USED` rate         | A spent-set outage forces fail-closed, which denies access   | §Failure modes |
| `T-P15-17` | **Credential replay**                           | Single-use; atomic redemption; `ReplayDetectionRecord`                                 | `CREDENTIAL_REPLAY_DETECTED` rate     | —                                                            | —          |
| `T-P15-18` | **Audit-stream joins** — the chain rebuilt from evidence | Six separately keyed, separately authorized streams; no cross-stream key; bundles for auditors | Stream authorization review | An incident-response tool granted everything at once         | PACK-12 + PACK-17 |
| `T-P15-19` | **Duplicate issuance**                          | Participation-unit ledger on the identity side; spent-nonce set on the voting side     | Duplicate-rejection counts            | A governed reissue is a legitimate second credential; it must be attributable | — |
| `T-P15-20` | **Silent reissue by an operator**               | No unattributed re-mint; governed reissue path with dual control                       | Reissue counts per context            | —                                                            | —          |

## 4. Credential handling

| #          | Threat                            | Preventive control                                                          | Detective control                        | Residual risk                                                             | Dependency |
| ---------- | --------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------- | ---------- |
| `T-P15-21` | **Credential theft**              | Short lifetime; single use; audience binding; no bearer semantics after use | Redemption anomalies                     | A stolen credential redeemed before the holder notices is unrecoverable **by design** | PACK-16 |
| `T-P15-22` | **Credential transfer / vote selling** | Non-transferable as far as technically enforceable — and no further      | Pattern detection on issuance and redemption | **Not solved.** Coercion resistance is a protocol property             | PACK-16    |
| `T-P15-23` | **Phishing of the voting origin** | Fixed origin; no caller-supplied redirect; governed communications never carry credential secrets | Reported look-alike domains | Users can be led to a look-alike site                          | FRONT-PACK + process |
| `T-P15-24` | **Malicious browser extension**   | Origin isolation limits what is observable                                  | —                                        | An extension in the page is inside the trust boundary. Named, not solved  | —          |

## 5. Eligibility integrity

| #          | Threat                                       | Preventive control                                                                | Detective control                  | Residual risk                                              | Dependency |
| ---------- | -------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------- | ---------- |
| `T-P15-25` | **Malicious eligibility denial**             | Reason-coded decisions; dispute path; `SD-08`; denial-rate monitoring by the auditor | Denial-rate anomalies per scope   | A plausible denial at scale is slow to detect              | Governance |
| `T-P15-26` | **Malicious eligibility approval**           | Rule-set freeze; `SD-04`; approval evidence; auditor sampling                     | Approval outside the rule-set      | An approved manual exception is legitimate-looking         | Governance |
| `T-P15-27` | **Small-group disclosure**                   | PACK-12 statistical disclosure control; minimum aggregation; suppression          | Disclosure-control checks          | A body of eleven people is inherently near-identifying     | PACK-12 + governance |
| `T-P15-28` | **Stale eligibility** — a decision outlives its facts | Freshness bounds per criterion; supersession before assertion issuance   | Staleness counters                 | A change inside the assertion's short lifetime             | —          |
| `T-P15-29` | **Compromised membership source**            | Predicates only; freshness bounds; source integrity is the source's obligation    | Cross-source inconsistency checks  | A compromised source produces correct-looking eligibility  | Membership domain |

## 6. Insider and governance

| #          | Threat                                    | Preventive control                                                        | Detective control               | Residual risk                                        | Dependency |
| ---------- | ----------------------------------------- | ------------------------------------------------------------------------- | ------------------------------- | ---------------------------------------------------- | ---------- |
| `T-P15-30` | **Insider collusion across the boundary** | `SD-06`; no grant spans both sides; dual control; auditor notification    | Privileged session evidence     | Two colluding humans with legitimate separate access | Process    |
| `T-P15-31` | **Credential revocation abuse**           | Cutoff maximums; dual control late; no participant-targeted revocation    | Late-revocation counts          | A fault-shaped mass revocation is hard to distinguish from abuse in the moment | Governance |
| `T-P15-32` | **False replay detection** denying access | Replay records carry evidence; dispute path `F-P15-05`; reason-coded      | False-positive rate             | A replay store fault denies a legitimate participant | §Failure modes |
| `T-P15-33` | **Forced abstention / denial of access**  | Fail-visibly; dispute path; context-level remedies; availability targets  | Failure-rate monitoring         | An outage across a whole window disenfranchises      | PACK-17    |

## 7. Compromise

| #          | Threat                              | Preventive control                                                                    | Detective control              | Residual risk                                                              | Dependency |
| ---------- | ----------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------ | -------------------------------------------------------------------------- | ---------- |
| `T-P15-34` | **Key compromise**                  | Separate keys and trust roots per function; rotation; scoped verification boundaries   | Key-use anomalies              | Compromise of the assertion key allows forged eligibility until rotation   | PACK-16 / KMS |
| `T-P15-35` | **Compromised eligibility service or credential issuer** | Each holds only its own half; neither can reconstruct the chain alone | Integrity stream               | A compromised issuer can mint credentials — a ballot-stuffing risk owned with PACK-16 | PACK-16 |
| `T-P15-36` | **Compromised Voting Client**       | No identity to steal; no membership data; no persistent identifier                     | Integrity monitoring; CSP reports | A compromised client can observe its own user's choice                  | PACK-16 / FRONT-PACK |

---

## 8. Threats deliberately out of scope, with owners

| Threat                                            | Owner   | Why not here                                                        |
| ------------------------------------------------- | ------- | ------------------------------------------------------------------- |
| Ballot tampering, ballot stuffing at cast time    | PACK-16 | Requires the casting protocol                                        |
| Tally manipulation                                | PACK-16 | Requires the tally protocol                                          |
| Coercion and vote-buying resistance               | PACK-16 | A protocol property, not a boundary property                         |
| Verifiability (individual and universal)          | PACK-16 | Same                                                                 |
| Denial-of-service and resilience engineering      | PACK-17 | Its own round                                                        |
| Network-level anonymity                           | PACK-17 | Not achievable at the application layer                              |
| Physical and organizational security of operators | Process | Named, not engineered here                                           |

**Nothing above is claimed to be mitigated by this round.** They are listed
so that the absence is deliberate and attributable rather than an
oversight.

---

## 9. Threats added and revised by the architecture correction (2026-07-31)

### 9.1 Revised

| #          | What changed                                                                                                                                     |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `T-P15-13` | **Timing correlation** now has specified controls with default values rather than a named intention: queued release, batching (120 s), minimum cohort *k* = 5, uniform release delay 30–300 s, `cohort_wait_max` 3600 s, coarsened timestamps (300 s; ≥ 3600 s for small electorates), randomized voting-side minting delay 5–30 s. Residual risk **reduced and bounded, not eliminated**; `OD-P15-02` is closed |
| `T-P15-21` | **Credential theft** is materially narrowed: credential material never appears on any surface outside WS-03, so there is nothing to intercept in email, SMS, a screenshot, a file or a URL. The residual is a device handed over or observed mid-visit |
| `T-P15-22` | **Credential transfer** is narrowed by the same delivery boundary; coercion resistance remains PACK-16's                                          |
| `T-P15-04` | **Persistent pseudonym across contexts** is narrowed: the pseudonym now never crosses the boundary in any artifact, so a voting-side compromise cannot observe one at all |

### 9.2 Added

| #          | Threat                                                                          | Asset                  | Attacker / failure                              | Boundary            | Preventive control                                                                                                                     | Detective control                        | Evidence      | Residual risk                                                              | Dependency        |
| ---------- | ------------------------------------------------------------------------------- | ---------------------- | ----------------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ------------- | -------------------------------------------------------------------------- | ----------------- |
| `T-P15-37` | **Queue side channel** — the issuance queue's own metadata re-creates the timing pair it exists to break | Unlinkability | Operational telemetry; a queue-depth dashboard; per-scope release metrics | `H-04` | Queue keyed on the assertion, never on a participant; cohort-size **class** only; no per-scope queue metric in a small electorate; timing-class logging; notification on the release schedule | Correlation-risk detection on cohort size and metric cardinality | `AS-04` | A determined observer of release batch sizes over a long window learns cohort structure | `OD-P15-02` review at implementation |
| `T-P15-38` | **Credential material escaping WS-03** — it is displayed, copied, mailed, cached, logged or captured in an error report | Ballot secrecy; non-transferability | Ordinary product convenience; a support flow; an APM agent; an assisted-channel screen share | `H-07`, `H-08` | Ten prohibited delivery channels; volatile memory only; no clipboard write; `no-store`; no APM inside WS-03; reason-code-only error reporting; no screen sharing during the exchange | Response and payload inspection; CSP violation reports; storage scan | `AS-03`, `AS-04` | A photograph of a screen mid-exchange, or a compromised device | FRONT-PACK |
| `T-P15-39` | **Evidence-bundle differencing** — two bundles, or a bundle and a total, reveal a suppressed cell | Small-cohort privacy | An auditor with arithmetic; an automated comparison tool | `H-12` | Complementary suppression across cells **and across time**; one context per bundle; pre-closure export restricted to non-outcome sections under dual control; bundle provenance recorded | Suppression-metadata review; bundle-comparison checks | `AS-05` | A sufficiently long series of bundles narrows small cells; mitigated by limiting pre-closure exports | PACK-12 disclosure control |

### 9.3 What the correction does **not** change

No threat is closed by this correction. `T-P15-12` (operator correlation),
`T-P15-14` (infrastructure metadata), `T-P15-18` (audit-stream joins) and
`T-P15-27` (small-group disclosure) keep their controls, their owners and
their residual risk unchanged, and remain the four this round takes most
seriously.
