# PACK-15 Voting Trust Boundary, Eligibility & Credential Separation — Specification + ADR Report

```text
PACK-15 SPECIFICATION + ADR COMPLETE
ARCHITECTURE CORRECTED
REPOSITORY_VERSION 0.14.0
CANON_VERSION 0.8.0
NO CODE CHANGED
NOT IMPLEMENTED
NOT PASS
```

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

This round produced **documents only**. No service was created, no module
written, no test added or changed, no CI configuration touched, no database
migration authored, no contract fixture altered, no cryptography
integrated, no HSM or KMS bound, no version moved and no canon amended.
`services/`, `tests/`, `.github/`, `scripts/`, `contracts/`, `packages/`
and `frontend/` are untouched — this archive contains no file from any of
them.

---

## 1. Baseline and register

|                        |                                                                                            |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| Baseline archive       | `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`              |
| Baseline status        | PACK-01 — PACK-14: FINAL PASS, external GitHub Actions verified                            |
| Corrected input        | `EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_SPEC_ADR.zip` |
| Repository version     | `0.14.0` — unchanged by this round                                                         |
| Canon version          | `0.8.0` — unchanged by this round                                                          |
| Register entry         | `FIR-ROADMAP-005`, status `approved` — **not moved by this round**                         |
| Authoritative register | `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`                                 |

### 1.1 The register was replaced, and the replacement was verified

The Master Future Implementation Register carried in this archive is
**`EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`**, installed at
the canonical repository path
`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`, SHA-256
**at the moment of adoption**
`f4f7336139d81b970f1d4834031ae519ca8245e2c846fb2c48ade2a6b7c8c00f`.

That digest is deliberately **not** recomputed. It is the proof that the
supplied V6 file was adopted byte-for-byte unchanged, and a proof about a
past moment stops being one the instant it is rewritten to match a later
file. The register has legitimately changed twice since: the PACK-15
implementation candidate round appended round record 1.18, moved
`FIR-ROADMAP-005` to `candidate` and updated `FIR-BASE-001`; and the
Prettier round reflowed its tables and blank lines without altering a
word. Section 12 records the register's **current** digest beside this
adoption-time one.

It **supersedes** the register version carried in the pre-correction
PACK-15 SPEC+ADR archive (SHA-256
`3de0d7187ee0f42aed980def83845a471408ff4c3e8487d4a8f517917e902cb5`, which
was the PACK-14 FINAL PASS copy carried forward unchanged).

**Verified before adoption, by full comparison:**

| Check                                                        | Result                                                   |
| ------------------------------------------------------------ | -------------------------------------------------------- |
| Lines removed from the superseded register                   | **0**                                                    |
| Lines added                                                  | 240                                                      |
| Prior FIR entries missing from V6                            | **none**                                                 |
| Prior FIR entries altered, reordered, reverted or restatused | **none**                                                 |
| FIR entry count                                              | 141 → **147**                                            |
| New entries                                                  | `FIR-OSS-001` … `FIR-OSS-006`, exactly as provided       |
| New round record                                             | Register §1.15, documentation-only, licensing            |
| New section                                                  | Register §29, open-source licensing and reuse governance |

V6 is **purely additive**: every prior entry is preserved byte-for-byte,
and the only additions are §1.15 and §29 with the six `FIR-OSS-*` entries.

**There is one canonical register copy in this archive and no standalone
second copy.** No competing canonical file exists at any other path, and no
file named after the V6 upload is carried separately.

**New FIR identifiers created by this round: none.** **FIR status changes
made by this round: none** — the six `FIR-OSS-*` entries arrive with the
status the register gives them and are untouched here.

---

## 2. What the architecture correction changed

Five implementation-blocking open decisions are closed. **No accepted
architecture decision was reversed.** ADR-089 … ADR-098 keep their
decisions; nine of them carry a correction note recording the closure in
the PACK-14 correction style.

Every closure was resolved in the direction that **tightens an existing
prohibition rather than relaxing one** — that was a selection criterion,
not a coincidence, and it is why the canon verdict is unchanged.

| Decision    | Closure                                                                                                                                                                                                                                                                                                                                                        |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OD-P15-01` | **Assertion Issuer boundary.** Separately bounded module and storage boundary inside the voting-trust service; separate signing keys and service credentials; structurally unable to read account, person-record or membership stores; consumes only minimized eligibility decisions; extractable later to a separate deployable **without a contract change** |
| `OD-P15-02` | **Timing-correlation controls.** Nine controls with reference defaults, permitted ranges and hard lower bounds; queued issuance as the only mode; **a cohort of one is never minted immediately**; explicit small-electorate policy; disclosure-control integration                                                                                            |
| `OD-P15-03` | **Context-scoped pseudonym.** Default **none**; permitted only for context-local exactly-once enforcement; unique per context; never reusable; **never exposed to WS-03 or any crossing artifact**; not reverse-resolvable through any API; governed retention and destruction                                                                                 |
| `OD-P15-04` | **Independent-auditor evidence bundle.** `EvidenceBundle` v1 with a closed list of eight sections, a normative prohibited-content list, nine validation checks, versioning rules, export authorization and complementary small-cohort suppression across cells **and across time**                                                                             |
| `OD-P15-07` | **Credential delivery.** Delivered only inside the isolated WS-03 boundary; ten prohibited channels; the ordinary workspace transmits only a one-time handoff artifact; single-visit issuance; accessible and assisted fallbacks preserve isolation and create **no helper custody**                                                                           |

### 2.1 The flow after the correction

```text
[WS-02]  eligibility decided → assertion minted → QUEUED → released → notified
         → participant initiates a one-time handoff and leaves
════════════════════════ trust boundary ════════════════════════
[WS-03]  handoff artifact redeemed → assertion (volatile memory)
         → minting delay → credential (volatile memory) → redeemed
         → minimum continuation capability
```

**Credential material never exists outside WS-03**, and the ordinary
workspace never holds an assertion or a credential at any point.

### 2.2 The reference defaults, in one table

| Parameter                      | Default      | Range                      | Hard lower bound |
| ------------------------------ | ------------ | -------------------------- | ---------------- |
| `issuance_mode`                | `queued`     | `queued` only              | —                |
| `timestamp_granularity`        | 300 s        | 60 s … 3600 s              | 60 s             |
| `release_delay_min` / `_max`   | 30 s / 300 s | 10–300 s / ≥4×min, ≤1800 s | 10 s / 60 s      |
| `batch_interval`               | 120 s        | 60 s … 900 s               | 60 s             |
| `batch_max_size`               | 250          | 50 … 2000                  | 50               |
| `minimum_cohort_size` (_k_)    | 5            | 3 … 50                     | 3                |
| `cohort_wait_max`              | 3600 s       | 600 s … 21600 s            | 600 s            |
| `minting_delay_min` / `_max`   | 5 s / 30 s   | 2–60 s / ≥3×min, ≤300 s    | 2 s / 10 s       |
| `small_electorate_threshold`   | 50           | 20 … 200                   | 20               |
| `disclosure_min_cell`          | 5            | ≥ 5                        | 5                |
| `issuance_window_min_duration` | 4 h          | ≥ 4 h (24 h if small)      | 4 h              |

An out-of-range configuration is **refused** with
`TIMING_PROFILE_OUT_OF_BOUNDS`, never clamped silently. Access is **never
denied for want of a cohort**: at `cohort_wait_max` the assertion releases
regardless, and the exception is recorded with a cohort-size _class_.

---

## 3. Documents in this archive

**Thirty-eight files: twenty-six PACK-15 documents, ten ADRs, this report,
and the V6 register.** Every PACK-15 document carries the
**Architecture correction applied (2026-07-31)** marker and names V6 as the
authoritative register.

### 3.1 Substantially rewritten

`PACK-15-SPECIFICATION.md` · `PACK-15-ASSERTION-MATRIX.md` ·
`PACK-15-CREDENTIAL-LIFECYCLE-MATRIX.md` · `PACK-15-REVOCATION-MATRIX.md` ·
`PACK-15-UNLINKABILITY-MATRIX.md` ·
`PACK-15-CROSS-BOUNDARY-DATA-FLOW-MATRIX.md` ·
`PACK-15-AUDIT-SEPARATION-MATRIX.md`

### 3.2 Extended with correction sections

`PACK-15-ACCEPTANCE-MATRIX.md` (§27) ·
`PACK-15-THREAT-MODEL.md` (§9) ·
`PACK-15-EVENT-CATALOG.md` (§9) ·
`PACK-15-REASON-CODE-CATALOG.md` (§9) ·
`PACK-15-API-CATALOG.md` (§10) ·
`PACK-15-FAILURE-MODE-MATRIX.md` (§6) ·
`PACK-15-RENDITION-SPECIFICATION.md` (§7) ·
`PACK-15-CONTENT-CATALOGUE-DE.md` (§12) ·
`PACK-15-WORKFLOW-MATRIX.md` (§6) ·
`PACK-15-PRIVACY-RETENTION-MATRIX.md` (§6–7) ·
`PACK-15-SEPARATION-OF-DUTIES-MATRIX.md` (§7) ·
`PACK-15-INTERMEDIATE-TALLY-PROHIBITION-MATRIX.md` (§6) ·
`PACK-15-FIR-COVERAGE-MATRIX.md` (§6) ·
`PACK-15-CANON-ASSESSMENT.md`

### 3.3 Marker and register line only

`PACK-15-ELIGIBILITY-MATRIX.md` ·
`PACK-15-ATTRIBUTE-MINIMIZATION-MATRIX.md` ·
`PACK-15-FORM-INVENTORY.md` · `PACK-15-FIELD-CATALOGUE.md` ·
`PACK-15-ATTACHMENT-MATRIX.md`

Their content required no change: minimization, forms and fields were
already stated as prohibitions, and the correction only tightened
prohibitions elsewhere.

---

## 4. ADRs — all preserved, nine annotated

| ADR     | Decision                                                                                     | Correction note                                                       |
| ------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| ADR-089 | Eligibility and credential issuance are separate authorities, stores, keys and audit streams | Assertion Issuer boundary fixed (`OD-P15-01`)                         |
| ADR-090 | One trust boundary; one artifact crosses; nothing exists on both sides                       | Crossing re-drawn via the one-time pickup (`OD-P15-07`)               |
| ADR-091 | The assertion carries a decision, not a person; closed list of twelve fields                 | Pseudonym removed entirely; queued release (`OD-P15-02`, `OD-P15-03`) |
| ADR-092 | The credential is opaque, single-use, context-bound; `redeemed` is absorbing                 | Delivery closed; single-visit issuance (`OD-P15-07`)                  |
| ADR-093 | **Set-not-map: no store contains both references**                                           | Timing residual now has controls and numbers (`OD-P15-02`)            |
| ADR-094 | Nothing may pre-empt the official tally, including telemetry                                 | Thresholds are numbers; pre-closure export restricted                 |
| ADR-095 | Revocation only before redemption, bounded by a cutoff, never targeted at a person           | Normative rule stated explicitly                                      |
| ADR-096 | WS-03 starts empty, leaves nothing behind, shares nothing in either direction                | Isolation now covers content as well as storage                       |
| ADR-097 | Six audit streams, never unified; the auditor works from bundles                             | The bundle is defined (`OD-P15-04`)                                   |
| ADR-098 | Disputes resolved without ballot content and without person→ballot linkage                   | unchanged — the correction did not touch it                           |

---

## 5. Revocation — the normative rule

1. **Before issuance, eligibility may be invalidated.**
2. **After issuance and before redemption, the credential may be revoked**,
   on governed conditions and before `RevocationCutoff`.
3. **After redemption, no person-level revocation and no ballot lookup is
   possible.**
4. **No identity-side operation may locate, delete, replace or invalidate a
   specific ballot.** None exists and none may be added.
5. **Any later election-wide invalidation belongs to PACK-16 governance and
   must not create identity linkage.**

One honest consequence of `OD-P15-07`: because issuance and redemption now
occur in a single WS-03 visit, the practical window of regime 2 is usually
seconds. The regime doing most of the work is therefore the **assertion**
regime, before pickup — which is also the one in which nothing is lost.

---

## 6. Participation-status minimization

| Status                       | Identity-side UI | Notifications | Identity domain may receive it |
| ---------------------------- | ---------------- | ------------- | ------------------------------ |
| Eligibility status           | **yes**          | yes           | yes                            |
| Issuance availability        | **yes**          | yes           | yes                            |
| Credential redemption status | **no**           | **no**        | **no**                         |
| Ballot cast status           | **no**           | **no**        | **no**                         |

No API returns redemption or cast status to the identity side, no event
carries it there, no projection derives it and no UI element has a slot for
it. **Notifications must not confirm whether a person participated.**
Operational redemption data stays inside the credential boundary and its
separated audit stream (`AS-03`), and is not exported to the identity side
even in aggregate — an aggregate scoped narrowly enough is a person-level
statement.

The prohibited code `ALREADY_VOTED` is joined by `PARTICIPATION_CONFIRMED`
for the same reason.

---

## 7. Acceptance, threats and FIR coverage after the correction

| Matrix              | Before | After   | Note                                                                                                                  |
| ------------------- | ------ | ------- | --------------------------------------------------------------------------------------------------------------------- |
| Acceptance criteria | 126    | **154** | All PASS blockers; **0** met by this round                                                                            |
| Threats             | 36     | **39**  | `T-P15-37` queue side channel, `T-P15-38` credential material escaping WS-03, `T-P15-39` evidence-bundle differencing |
| API operations      | 34     | **40**  | None implemented, none routed, no transport bound                                                                     |

FIR treatments: addressed 8 · partially addressed 25 · deferred 5 ·
unchanged 21 · **implemented 0**. `FIR-CONFIG-001` moves from deferred to
partially addressed because the `IssuanceTimingProfile` is now governed
configuration with ranges and hard lower bounds rather than constants.

**`FIR-OSS-001` … `FIR-OSS-006` are `unchanged` by this round.** PACK-15
selects no licence, publishes no source, generates no SBOM, accepts no
contribution and makes no release. Nothing here may be read as licensing
compliance or as a claim that any `FIR-OSS-*` obligation is met; the
register's own §29 boundaries apply and are not narrowed.

---

## 8. Canon assessment

```text
CANON AMENDMENT NOT REQUIRED
```

`CANON_VERSION` remains `0.8.0`; the canon file is neither modified nor
included. Each of the five closures raises a canonical question and each is
answered **no**: a module boundary inside a service is not a canonical
ownership change; `IssuanceTimingProfile` is governed configuration, not an
aggregate; the pseudonym became _less_ canonical, not more; the evidence
bundle is a pack-level export format under ADR-074's evolution rules; and
restricting delivery adds a prohibition to canon 10.1 rather than changing
its shape.

The register's new §29 and its `FIR-OSS-*` entries are licensing
obligations. Licensing governs the distribution of software; the canon
governs the domain event model. They do not intersect.

---

## 9. Open decisions after the correction

| ID          | Status     | Owner          | Must close by             |
| ----------- | ---------- | -------------- | ------------------------- |
| `OD-P15-01` | **closed** | —              | —                         |
| `OD-P15-02` | **closed** | —              | —                         |
| `OD-P15-03` | **closed** | —              | —                         |
| `OD-P15-04` | **closed** | —              | —                         |
| `OD-P15-05` | open       | **PACK-16**    | PACK-16 specification     |
| `OD-P15-06` | open       | **PACK-09**    | Before production         |
| `OD-P15-07` | **closed** | —              | —                         |
| `OD-P15-08` | open       | **Governance** | Before first advisory use |

None of the three remaining blocks acceptance of this specification, and
none may be closed by an implementation making a choice quietly.

---

## 10. Implementation dependencies

| Dependency                                                                 | Owner                          |
| -------------------------------------------------------------------------- | ------------------------------ |
| Ballot casting, verification, tally, cryptographic voting protocol         | PACK-16                        |
| Coercion resistance, receipt-freeness, verifiability                       | PACK-16                        |
| Advance credential issuance across visits                                  | PACK-16 (`OD-P15-05`)          |
| Voting Client construction and its page structure                          | FRONT-PACK + PACK-16           |
| Network-level correlation, resilience, incident readiness                  | PACK-17                        |
| Backup and restore topology separation                                     | PACK-17 + operations           |
| Retention schedules                                                        | PACK-09 (`OD-P15-06`)          |
| Privileged access, dual control, break-glass, disclosure control           | PACK-12 (reused unchanged)     |
| Governed rules registry for eligibility rule-sets                          | `FIR-RULE-001`                 |
| Governed operational configuration for the timing profile                  | `FIR-CONFIG-001`               |
| Canonical forms framework and governed content store                       | `FIR-FORM-001`, `FIR-FORM-004` |
| Official delivery evidence                                                 | `FIR-DELIVERY-001`             |
| HSM / KMS binding for assertion, credential, bundle, ballot and tally keys | Deployment + PACK-16           |
| Open-source licensing, SBOM, provenance, trademark and release process     | `FIR-OSS-001` … `FIR-OSS-006`  |

---

## 11. Consistency checks performed

| Check                                                                                                                       | Result                     |
| --------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| No account ID, person record ID, membership ID or member number in the assertion                                            | pass                       |
| No communication persona in the assertion                                                                                   | pass                       |
| **No context-scoped pseudonym in any crossing artifact**                                                                    | pass                       |
| No raw identity data in the credential                                                                                      | pass                       |
| No credential ID reused as a ballot ID                                                                                      | pass                       |
| No Voting Client identity session specified                                                                                 | pass                       |
| No shared cookies or storage specified for WS-03                                                                            | pass                       |
| **No credential material on any surface outside WS-03**                                                                     | pass                       |
| No reusable cross-origin bearer token specified                                                                             | pass                       |
| No unified audit chain specified                                                                                            | pass                       |
| No store, log, event or stream holding both an assertion and a credential reference                                         | pass                       |
| No intermediate tally surface specified                                                                                     | pass                       |
| No cast-status exposure to the identity domain                                                                              | pass                       |
| No automatic ballot revocation after redemption                                                                             | pass                       |
| No single-service visibility across identity, credential, ballot and tally                                                  | pass                       |
| **Register V6 is purely additive: 0 lines removed, all 141 prior entries intact**                                           | pass                       |
| **Exactly one canonical register copy in the archive**                                                                      | pass                       |
| No code in the archive                                                                                                      | pass — 38 files, all `.md` |
| No tests, CI, migrations or contract fixtures in the archive                                                                | pass                       |
| No repository version change                                                                                                | pass — `0.14.0` throughout |
| No canon version change                                                                                                     | pass — `0.8.0` throughout  |
| No new `FIR` identifier and no `FIR` status change made by this round                                                       | pass                       |
| Every document carries the round banner, the correction marker and NOT PRODUCTION READY                                     | pass                       |
| No affirmative production-readiness or legal-activation claim anywhere                                                      | pass                       |
| Every internal reference resolves — documents, ADRs, `AC-`, `T-P15-`, `SD-`, `AS-`, `H-`, `FM-`, `EC-`, `F-P15-`, `OD-P15-` | pass                       |
| Status remains `NOT IMPLEMENTED / NOT PASS`                                                                                 | pass                       |

---

## 12. SHA-256 of every file in this archive

**Recomputed 2026-07-31, after the Prettier formatting round.** Every
digest below is the SHA-256 of the file as it exists in the current
cumulative candidate archive. Thirty-six of the thirty-seven entries were
still valid before that round; Prettier reflowed thirty-three of them
(tables, blank lines and emphasis markers only, no word changed), and the
register had already moved for the reasons given in section 1.1. The
digests are recomputed rather than left stale so that this manifest keeps
saying something true about the files shipped beside it.

| File                                                                  | SHA-256                                                                                          |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `docs/adr/ADR-089-ELIGIBILITY-AND-CREDENTIAL-SEPARATION.md`           | `1f267f9babeeb1f383e3f44d9dacb6d35eb2d76a98ff6603a83b617d283ed6d9`                               |
| `docs/adr/ADR-090-VOTING-TRUST-BOUNDARY.md`                           | `37f9d4b65eb5561bd13ce072000a8549e082e2bae5227fa3d99dfced20032c90`                               |
| `docs/adr/ADR-091-MINIMIZED-ELIGIBILITY-ASSERTION.md`                 | `ff849a9e13b12f7cdf1191c0ab1d87a9f437117f8570333842e3d8a0a7371ae0`                               |
| `docs/adr/ADR-092-VOTING-CREDENTIAL-LIFECYCLE.md`                     | `1d9ee94f3b99fcb972ff951f7e0560ab5a7f44d35a0988466f86ac05a768116e`                               |
| `docs/adr/ADR-093-UNLINKABILITY-AND-NON-CORRELATION.md`               | `a8b303a6c13c9e2a9373c2699943346233b856dec49b5f155027ef8378d29a05`                               |
| `docs/adr/ADR-094-NO-INTERMEDIATE-TALLY.md`                           | `e63570cc2fe17e4437797eb6279c00a547c0a1200d4d28d41a7be0e68fea3b1f`                               |
| `docs/adr/ADR-095-REVOCATION-BEFORE-REDEMPTION.md`                    | `6c78556fc45de8cac8caad00a2e7aebfa42dae2d272dca4d5b7c68d37a74c553`                               |
| `docs/adr/ADR-096-VOTING-CLIENT-ISOLATION.md`                         | `e0fafde6859c29d29e0acff729ded88f4b183c5c6f8206adc237ae53f70cd78d`                               |
| `docs/adr/ADR-097-VOTING-AUDIT-SEPARATION.md`                         | `3c89478c013f491c92987d9f784a1621ba29937070a884d14c09e43030c459fc`                               |
| `docs/adr/ADR-098-DISPUTE-HANDLING-WITHOUT-BALLOT-LINKAGE.md`         | `867a9c9dc70592523c05d9dbcc0dc53ae7007446c6b66fd5b01edd1ef32f28c8`                               |
| `docs/packs/PACK-15/PACK-15-ACCEPTANCE-MATRIX.md`                     | `8e42ae8362af3fe9268f74624e4a30ebdfb8383ae9228a74160733775430b414`                               |
| `docs/packs/PACK-15/PACK-15-API-CATALOG.md`                           | `7a9b231e0f22ca797fa83da32418b8dbe74c6c08ebb6a0c5ff845583d3bd379d`                               |
| `docs/packs/PACK-15/PACK-15-ASSERTION-MATRIX.md`                      | `13341631a6c04804bd9a6436034fd775fd2e5d18e2a3a3f0af508b753da91dc1`                               |
| `docs/packs/PACK-15/PACK-15-ATTACHMENT-MATRIX.md`                     | `4f6ee602d3dabe290337a647241e029f106e6af3f3674e507d514a44dd6cf390`                               |
| `docs/packs/PACK-15/PACK-15-ATTRIBUTE-MINIMIZATION-MATRIX.md`         | `17819384871b7378e689a123c9f978964647a565b95d9616ef3027e1dfd2324f`                               |
| `docs/packs/PACK-15/PACK-15-AUDIT-SEPARATION-MATRIX.md`               | `7c1fbffbbc0ac9ddefeaa80b9ea0d419b369290b107cb4a41c86055f41db379f`                               |
| `docs/packs/PACK-15/PACK-15-CANON-ASSESSMENT.md`                      | `b27f6cc0bc6ecdc166e91618b8abdb2c4d737db3896b5ca019396ada4f4e0270`                               |
| `docs/packs/PACK-15/PACK-15-CONTENT-CATALOGUE-DE.md`                  | `3ad6445b0e6c72bfe7bd2561fa353fc39d537cc284cd50f13efe1dd49bc36338`                               |
| `docs/packs/PACK-15/PACK-15-CREDENTIAL-LIFECYCLE-MATRIX.md`           | `4abf38021ecf6f73886623f3ae6a717f591733e01ab158239f7c7af04fd8d297`                               |
| `docs/packs/PACK-15/PACK-15-CROSS-BOUNDARY-DATA-FLOW-MATRIX.md`       | `c8dd71de166caabe6a1c65daeef0bed70c1ad640026d8190ede0c9471a809445`                               |
| `docs/packs/PACK-15/PACK-15-ELIGIBILITY-MATRIX.md`                    | `e4aa41a1175fc9345a62ec19ae44630ff8be778e77592e89c5c2e25cf3501af8`                               |
| `docs/packs/PACK-15/PACK-15-EVENT-CATALOG.md`                         | `75c77841cfdb63031f7c1e8eb075dff0819bec8b86a94e60dd2193fbaf0e13df`                               |
| `docs/packs/PACK-15/PACK-15-FAILURE-MODE-MATRIX.md`                   | `7b585b43be2a1104027e52acf0c2c403f9d5b3f4fcdb00d0b83536c3ef2055c7`                               |
| `docs/packs/PACK-15/PACK-15-FIELD-CATALOGUE.md`                       | `8cf2f0bae204c77e1b8bc6990eebed142dedb2fa399aefdc865614ba6ef8dd8a`                               |
| `docs/packs/PACK-15/PACK-15-FIR-COVERAGE-MATRIX.md`                   | `c6a0226dba5d705abdba75f2a148e54a3346ed70627e3d882bd6bd29a8b9ce5b`                               |
| `docs/packs/PACK-15/PACK-15-FORM-INVENTORY.md`                        | `7cd981a6035b2ca2898379723c56e0c7d59015561f7a5ec577eed5cb39e2ab74`                               |
| `docs/packs/PACK-15/PACK-15-INTERMEDIATE-TALLY-PROHIBITION-MATRIX.md` | `3b3230c7e93a2c93436a9cb237456110899f24a3aa54c2490d4f696fca0c6f01`                               |
| `docs/packs/PACK-15/PACK-15-PRIVACY-RETENTION-MATRIX.md`              | `1bacb6c0398169dd8470df1e3f0df18e5f48b33d46ac8f6a901084fba94b8f74`                               |
| `docs/packs/PACK-15/PACK-15-REASON-CODE-CATALOG.md`                   | `eb2f7b7b747d62cb81d3082d15bac35ae67bd052c195c4a8ef5e72f2cb4fa7de`                               |
| `docs/packs/PACK-15/PACK-15-RENDITION-SPECIFICATION.md`               | `ec074dfe97f64a6e66097ffbc1d39a17cdf3742e8a1ce8c51096d38845c70e73`                               |
| `docs/packs/PACK-15/PACK-15-REVOCATION-MATRIX.md`                     | `4585f45c40790629e1301d124f3ee8cbf32c037c7cbab8867810d21d1282ce08`                               |
| `docs/packs/PACK-15/PACK-15-SEPARATION-OF-DUTIES-MATRIX.md`           | `83cf049cb9825778c93b1999b3b190f23d6996f74cefb1e432fc180a9ecdbd43`                               |
| `docs/packs/PACK-15/PACK-15-SPECIFICATION.md`                         | `bf3a3255a8d9b5f044f68150d75cc8b929d6cc94a3ff9ed03e4defaf613db0ac`                               |
| `docs/packs/PACK-15/PACK-15-THREAT-MODEL.md`                          | `b77a875e67cfca81deece8192576829c02684e491937563b65234bed2eddef08`                               |
| `docs/packs/PACK-15/PACK-15-UNLINKABILITY-MATRIX.md`                  | `e582f1fbf5eac93aaa45930a22d401796a02dcdfcdc00b2c8c97f5072acbf172`                               |
| `docs/packs/PACK-15/PACK-15-WORKFLOW-MATRIX.md`                       | `842b04fc19e449230134cc257b4b729ac7b0f34d4934497315deeb801e9e1d1a`                               |
| `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`          | `aac89def1a59ad43e8d39332f0bde4bfdc3a807a053b0eb06113ac8d1b8012c8`                               |
| `docs/handover/PACK-15-SPEC-ADR-REPORT.md`                            | _self-referential — a file cannot contain its own digest; compute it from the delivered archive_ |

**The load-bearing digest** is the register's,
`f4f7336139d81b970f1d4834031ae519ca8245e2c846fb2c48ade2a6b7c8c00f`, which
must equal the SHA-256 of the supplied
`EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`, proving that
the file was adopted unchanged and that no second canonical copy diverges
from it.

## 13. Archive digest

The SHA-256 of the delivered archive is reported in the delivery message
accompanying it, and is deliberately not printed here: a file cannot
contain the digest of the archive that contains it.

```bash
sha256sum EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_SPEC_ADR_ARCHITECTURE_CORRECTED.zip
```

---

## 14. What this round is not

It is not an implementation. It is not a candidate. It is not a PASS. It
creates no service, module, migration, test, contract fixture or CI stage.
It changes no version and amends no canon. It integrates no cryptography,
no HSM and no KMS. It selects no voting protocol. It completes no
licensing and claims no `FIR-OSS-*` compliance. It does not cast a ballot,
count a vote, build a Voting Client, or make this system usable for a
public election — the `public_election_profile` context type exists so the
architecture does not foreclose one, and **nothing here activates it,
permits it or claims it.**

It draws one boundary carefully, says exactly what is on each side, and now
also says exactly how long the crossing waits and where the crossing may
never be written down.

```text
PACK-15 SPECIFICATION + ADR COMPLETE
ARCHITECTURE CORRECTED
REPOSITORY_VERSION 0.14.0
CANON_VERSION 0.8.0
NO CODE CHANGED
NOT IMPLEMENTED
NOT PASS
```

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

**Do not proceed to implementation without a separate task.**
