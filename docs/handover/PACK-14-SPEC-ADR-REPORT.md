# PACK-14 Identity, Authentication & Account Security — Specification + ADR Report

```text
PACK-14 SPECIFICATION + ADR COMPLETE
ARCHITECTURE CORRECTED
REPOSITORY_VERSION 0.13.0
CANON_VERSION 0.8.0
NO CODE CHANGED
NOT IMPLEMENTED
NOT PASS
```

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

This round produced **documents only**. No service was created, no module
written, no test added or changed, no CI configuration touched, no database
migration authored, no provider integrated, no version moved and no canon
amended. `services/`, `tests/`, `.github/`, `scripts/`, `contracts/` and
`frontend/` are untouched.

---

## 1. Baseline

|                        |                                                                                          |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| Baseline archive       | `EPD2_PACK-13_PRODUCTION_DATA_PLANE_CONTRACT_EVOLUTION_0.13.0_FINAL_PASS.zip`            |
| Baseline status        | PACK-01 — PACK-13: FINAL PASS, external GitHub Actions verified                          |
| Repository version     | `0.13.0` — unchanged by this round                                                       |
| Canon version          | `0.8.0` — unchanged by this round                                                        |
| Authoritative register | Included in this archive at `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` |

### The register included in this archive is the cumulative one

`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` is carried in
this archive at its canonical repository path. It is the **cumulative
Master Future Implementation Register taken from the PACK-13 FINAL PASS
archive** — SHA-256
`8d35a7551a28d1156fd8f2c66e37c4db4659589cf46e4f7e2ee83a161115c278` — with
the `FIR-UX-011` additions merged into it.

**It is not the standalone V5 file.** An earlier revision of this archive
carried standalone V5 byte-for-byte, and that was wrong: V5 was authored
against the register as it stood _before_ the PACK-13 FINAL PASS round, so
using it as a replacement would have silently dropped four things that round
recorded — its round record, the `FIR-BASE-001` baseline pointer, the
`FIR-ROADMAP-003` status update, and the section 21 summary. A register that
loses a completed round's status is worse than one missing a future
obligation, so the cumulative file is the base and V5 supplies only its
additions.

**What was added to the cumulative register, and nothing else:**

| Addition                                                                                                               | Placement                                                                                                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The documentation-only round record for Page Specification and Screen Content Governance                               | **§1.14** — supplied as §1.13, recorded here as §1.14 because §1.13 in the cumulative register is already the PACK-13 FINAL PASS round record. No word of its content changed and nothing existing was renumbered |
| **`FIR-UX-011` — Page Specification and Screen Content Governance**                                                    | Section 28, before that section's boundaries block                                                                                                                                                                |
| One sentence in section 21 naming `FIR-UX-011`'s page and screen catalogue among what is specified but not implemented | The necessary summary reference                                                                                                                                                                                   |

**Nothing was removed, reverted or overwritten.** A line-by-line comparison
against the PACK-13 FINAL PASS register shows exactly three deviations: two
pure insertions and the one section 21 sentence, which is extended rather
than replaced. All 140 entries of the cumulative register survive and
`FIR-UX-011` makes 141, with no duplicate identifier.

**No PACK-13 status was reopened or changed.** `FIR-ROADMAP-003` still reads
`implemented in reference form`; `FIR-BASE-001` still names
`EPD2_PACK-13_PRODUCTION_DATA_PLANE_CONTRACT_EVOLUTION_0.13.0_FINAL_PASS.zip`
as the authoritative cumulative baseline; §1.13's PACK-13 FINAL PASS round
record is untouched; and section 21 still records PACK-01 through PACK-13 as
PASS.

**This is the authoritative cumulative Master Future Implementation Register
for PACK-14 and every subsequent PACK.** It carries `FIR-PROG-003`,
`FIR-FORM-001` … `FIR-FORM-005`, `FIR-RULE-001`, `FIR-REF-001`,
`FIR-DELIVERY-001`, `FIR-TRUST-001`, `FIR-REPRESENT-001`,
`FIR-INCLUSION-001`, `FIR-QUALITY-001`, `FIR-CONFIG-001`, `FIR-IMPORT-001`,
`FIR-SERVICE-001` and `FIR-UX-003` … **`FIR-UX-011`**.

**PACK-14 itself changes no entry in it.** A specification round has nothing
to record there yet: no status moves, no identifier is created by this pack,
no entry is deleted and no second register exists. What each entry _will_
receive is recorded in `PACK-14-FIR-COVERAGE-MATRIX.md`, and nothing there
is marked `implemented`.

## 2. Documents created

**1 register**, `docs/roadmap/`: the cumulative Master Future
Implementation Register from PACK-13 FINAL PASS, extended with
`FIR-UX-011` and nothing else.

**22 pack documents**, `docs/packs/PACK-14/`: specification, acceptance
matrix, threat model, identity separation matrix, authentication method
matrix, assurance level matrix, session security matrix, recovery control
matrix, identity proofing matrix, cross-workspace session matrix, event
catalog, reason code catalog, FIR coverage matrix, canon assessment, and
the seven forms-layer documents (form inventory, field catalogue, German
content catalogue, workflow matrix, attachment matrix, rendition
specification, privacy and retention matrix).

**10 ADRs**, `docs/adr/`: ADR-079 through ADR-088, all `proposed`.

**1 handover report**, this document.

**33 files in total.**

## 2.1 Architecture correction — the ten resolutions

Nine of ten implementation-blocking open decisions are closed in this
revision; the tenth is open by design and does not block. **No accepted
architecture decision was reversed** — ADR-079 … ADR-088 keep their
decisions, and six carry a note recording what their open questions resolved
to.

| #   | Decision                             | Resolution                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| --- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | **Account lifecycle representation** | The canonical `AccountStatus` enum is **not** extended. `locked`, `closure_pending` and `deleted_or_anonymized` appear in no normative status list: a technical lock is an **`AccountLock`** record, a security quarantine an **`AccountRestriction`** of the security class, closure-pending a state of **`AccountClosureRequest`**, and anonymization or deletion **lifecycle outcomes and events**. Several may hold at once on an `active` account, each separately queryable and reversible |
| 2   | **Bounded-context ownership**        | **`identity-service` owns all six** — Account Registry, Credential Registry, Authentication, Session Security, recovery coordination, identity-proofing references — as internally separated modules with separate storage boundaries. **No parallel authentication service.** Canonical ownership of `Account` and `IdentityRecord` unchanged                                                                                                                                                   |
| 3   | **Password fallback**                | **Supported, controlled.** Passkeys preferred; no new password-only account; never sole assurance for a consequential action; MFA always; ceiling `substantial`; disableable through governed configuration; security questions still prohibited                                                                                                                                                                                                                                                 |
| 4   | **Session and freshness defaults**   | Governed configuration with safe defaults: `low` 30 min / 7 d, `substantial` 30 min / 24 h, `high` 15 min / 8 h; step-up 15 min, ordinary submission 60 min, security or contact change 15 min. Stricter freely; relaxation governed; **no deadline removable**; nothing may disable step-up, audit or separation of duties                                                                                                                                                                      |
| 5   | **Session model**                    | `SessionRecord` is a **PACK-14 service-level aggregate**, not canon, on PACK-12 `PrivilegedSession`'s precedent; events use PACK-13's envelope                                                                                                                                                                                                                                                                                                                                                   |
| 6   | **Cross-origin bootstrap**           | Each workspace runs **its own ceremony**; `identity-service` returns a **single-use, short-lived, audience-bound authorization response**; the workspace mints its **own origin-local session**. No parent-domain cookie, no reusable cross-origin token, no shared browser-storage identity; higher-risk boundaries require new authentication or step-up. **This is not SSO and is nowhere described as a shared application session**                                                         |
| 7   | **Voting handoff**                   | The outbound **`VotingHandoffArtifact`**: opaque, single-use, short-lived, audience-bound, purpose-bound, voting-context-bound, carrying no account, person, membership, persona or contact identifier, with no reusable bearer semantics and no reverse identity resolution. Eligibility assertion, credential issuance, ballot and tally stay outside PACK-14                                                                                                                                  |
| 8   | **Passkey attestation**              | No universal attestation; **synced passkey caps at `substantial`**; `high` needs a device-bound credential or an approved equivalent; hardware attestation only for governed privileged action classes; **no ordinary member excluded for lack of it**                                                                                                                                                                                                                                           |
| 9   | **SMS OTP**                          | **Not a login method, not a step-up factor, carries no assurance level.** Phone-channel verification and a low-weight recovery signal only. **The system operates with no SMS provider.** Every contradictory AAL mapping removed                                                                                                                                                                                                                                                                |
| 10  | **Recovery assurance**               | Recovery **may** use different evidence; the **resulting confidence** must be equivalent or carry a reason-coded risk acceptance; high-assurance recovery requires **dual control, cooling-off and out-of-band notification, all three**; emergency recovery restores access but **cannot immediately authorize high-risk actions**; credentials and sessions are revoked **before** completion                                                                                                  |

### Why these resolutions needed no canon amendment

Each was resolved in the direction that leaves canon untouched, and that was
a selection criterion rather than luck. Extending `AccountStatus`,
canonising `SessionRecord` or fixing a canonical handoff form would each
have required an amendment; none was necessary to make the architecture
implementable. `CANON_VERSION` stays `0.8.0` and the verdict remains
**CANON AMENDMENT NOT REQUIRED**.

## 3. Accepted architectural decisions

| ADR     | Decision                                                                                                                                                                                                                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ADR-079 | **No global user identity.** No identifier correlates a person across domains; no existing identifier is repurposed into one; correlation exists only through governed mapping boundaries carrying purpose, scope, owner, policy, retention, evidence and an explicit prohibition on uncontrolled correlation |
| ADR-080 | **Account, person record, membership, applicant and communication persona are five separate identity layers**, each with its own identifier space, owner and lifecycle                                                                                                                                        |
| ADR-081 | **Passkey-first authentication.** Multiple credentials per account; synced ≠ device-bound; attestation not universally required; removing the last credential is guarded                                                                                                                                      |
| ADR-082 | **Assurance and step-up are per action, not per login**, on canon's existing four-value scale, bound to the object version, evaluated fail-closed                                                                                                                                                             |
| ADR-083 | **Session security and cross-workspace isolation.** Workspace-scoped sessions, mandatory rotation, idle and absolute timeouts, revocation that cannot refresh, refresh-token reuse treated as replay, no storage identity bridge                                                                              |
| ADR-084 | **Account lifecycle and credential governance.** Technical lock, security quarantine, membership suspension and voluntary closure are never the same state; contacts are attributes, never identifiers                                                                                                        |
| ADR-085 | **Recovery is a governed workflow, not a support action.** Not weaker than what it replaces; no single actor completes it; no security questions; cooling-off; evidence; dispute                                                                                                                              |
| ADR-086 | **Identity proofing is a bounded case, not a person database.** Authentication ≠ proofing ≠ membership eligibility ≠ authorization; `person_record_id` is optional and is not an integration key                                                                                                              |
| ADR-087 | **Privileged identity administration reuses PACK-12 and adds no console.** Six roles with explicit separations; support is not ownership; no self-approval; no standing superuser                                                                                                                             |
| ADR-088 | **The voting handoff carries no identity**, is one-time, purpose-scoped, short-lived, audience-restricted and irreversible; PACK-14 defines the boundary and not the voting credential protocol                                                                                                               |

## 4. Identity separation summary

Five identifier spaces — `account_id`, `person_record_id`,
`membership_id`/`member_number`, the applicant reference and
`communication_persona_id` — plus a purpose-scoped actor reference that is
what domains and events actually carry. The voting credential is a sixth
space owned entirely by PACK-15/16.

Forbidden as universal or join keys: email, phone, member number,
`account_id`, `person_record_id`, national ID, eID subject identifier,
device identifier, communication persona identifier, and any
provider-issued stable subject claim.

An account may exist with no person record and no membership; a membership
may exist with no account; an applicant never becomes a member
automatically (canon 19d.9 stage B); two accounts are never merged by
matching email, name or date of birth.

## 5. Authentication and session summary

Passkeys are preferred and multiple credentials per account are expected.
Every other method carries an explicit assurance class and explicitly
restricted allowed actions; email and SMS are never sufficient for
high-risk actions. Whether a password fallback exists at all is an open
decision.

Assurance uses **canon's existing `none`/`low`/`substantial`/`high`
scale** — informally AAL-0 … AAL-3 — and no second scale is introduced.
Every consequential action declares a required assurance and a freshness
window; step-up is bound to the action and to the object version and is
void if the object changes; evaluation is fail-closed and conjunctive,
exactly as canon 19d.8 requires.

Sessions are workspace-scoped and never span a risk boundary. Rotation
after authentication, step-up and privilege change; both idle and absolute
timeouts; revoke one and revoke all; a revoked session cannot refresh;
refresh-token reuse revokes the family and raises a security event; no
session identifier in a URL; CSRF strategy required; no parent-domain
cookie and no browser-storage identity bridge.

WS-03 shares nothing at all. Entry is by a one-time, purpose-scoped,
short-lived, audience-restricted handoff that carries **no identity** and
cannot be reversed to the account that obtained it.

## 6. Recovery summary

A nine-step governed workflow: requested → risk assessed → alternate
verification → cooling-off → old credentials revoked → sessions revoked →
new credential enrolled → out-of-band notification → completed.

Recovery is not weaker than the authentication it replaces without a
reason-coded risk acceptance by a named authority. No support agent
completes it alone; no reviewer approves their own action. **No security
questions and no reliance on publicly discoverable personal facts** — for
candidates and office-holders those facts are campaign material. A recently
changed contact cannot be the sole basis. Completion revokes prior
credentials and every session. Evidence is produced, and a dispute path
exists.

## 7. Forms coverage summary

Required by `FIR-FORM-002`. Fifteen forms — registration, email and phone
verification, passkey enrollment and removal, MFA enrollment and removal,
recovery code issuance, recovery request, suspicious-login confirmation,
contact change, session revocation, account closure, identity proofing
submission, privileged recovery approval — each with fields, validation,
dependencies, declarations, workflow, attachments, renditions and a
retention class.

`PACK-14-CONTENT-CATALOGUE-DE.md` carries **real German texts** for every
key screen, declaration, confirmation, warning and refusal, versioned
`P14-DE-1.0.0` with an owner and an effective date. There is no
placeholder text anywhere.

Every submission produces an immutable receipt carrying form ID and
version, submission ID, time, submitting party, organizational scope,
attachment inventory, confirmed declarations, integrity reference, channel
and next procedural step. A form change never alters an already submitted
request.

**Deferred:** paper equivalents for the assisted and offline channels,
named rather than omitted.

## 8. FIR coverage

`PACK-14-FIR-COVERAGE-MATRIX.md` records **addressed 9, partially
addressed 21, deferred 5, unchanged 8, implemented 0.**

`FIR-INV-001` (no global user ID) is addressed most directly of all; the
voting-related invariants `FIR-INV-002` and `FIR-INV-003` are partially
addressed — PACK-14 supplies the identity-free handoff boundary and leaves
the credential protocol to its owner. Every entry from the PACK-13 register
addenda is assessed, including all eight frontend-governance entries.

**No FIR is marked implemented, and no new FIR identifier is created.**

### `FIR-UX-011` — the page sequence is explicitly not defined here

The Master Register supplied for this correction adds **`FIR-UX-011` — Page
Specification and Screen Content Governance**, which requires an approved
Page Specification Catalogue and Screen-State Matrix before any user-facing
domain counts as fully designed. PACK-14 treats it as **partially
addressed**, and the split is worth stating exactly, because it is the
difference between a specification and a guess.

PACK-14 supplies the **domain side** of `FIR-UX-011`'s own responsibility
split: the process, the authoritative data sources, the permissions and the
required assurance per action, the fifteen forms and their official
documents, the decisions, the mandatory governed German content, and the
colour-independent state semantics each surface must carry.

PACK-14 supplies **none of the frontend side** and produces **none** of the
ten artefacts `FIR-UX-011` names — `PAGE-CATALOGUE.md`,
`PAGE-SEQUENCE-MAP.md`, `NAVIGATION-MAP.md`, `CONTENT-MAP.md`,
`ACTION-MAP.md`, `SCREEN-STATE-MATRIX.md`,
`PERMISSION-AND-ASSURANCE-MATRIX.md`,
`RESPONSIVE-LAYOUT-SPECIFICATION.md`, `ACCESSIBILITY-FLOW.md`,
`ACCEPTANCE-SCREENSHOT-INVENTORY.md`.

**The complete first-page-to-final-page structure — entry screen,
subsequent pages, decision points, branch conditions, return and
cancellation paths, interrupted-process recovery, completion page and
receipt page — will be defined during the relevant `FRONT-PACK
Specification + UX/IA` stage, before frontend implementation.** A
FRONT-PACK implementation candidate must not begin before that catalogue,
page sequence, content map and state matrix are accepted.

The reason PACK-14 stops here is the one `FIR-UX-011` gives itself: a
domain PACK that invented the page order would settle information
architecture from outside the pack that owns it, and a FRONT-PACK that
inherited no process, permissions or governed content would invent them in
code. Both failures are avoided by each pack supplying only its own half —
which is why `AC-P14-104` makes the split itself a PASS-blocking
criterion.

## 9. Canon assessment

```text
CANON AMENDMENT NOT REQUIRED
```

The reasoning, in full in `PACK-14-CANON-ASSESSMENT.md`: canon 19d.2 and
19d.8 already fix the assurance scale, the five never-interchangeable
concepts, the step-up policy entity and its fail-closed conjunctive
evaluation; canon 7.2 and 7.3 already define `Account` and `IdentityRecord`
with their owners; canon 19d.9 already fixes the two-stage membership
boundary. PACK-14 reuses all of them and introduces no competing
vocabulary.

The single decision that most preserves this is refusing to invent an
AAL-0 … AAL-3 enum beside canon's four values. A second scale would have
been a canon amendment disguised as a convenience.

## 10. Open implementation decisions

**Nine of ten closed. One open by design.**

| ID            | Question                                                            | Status                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| OD-P14-01     | Where do `locked`, `closure_pending`, `deleted_or_anonymized` live? | **Closed** — not statuses at all; `AccountLock`, `AccountRestriction`, `AccountClosureRequest`, lifecycle outcomes                                                                                                                                                                                                                                                                                                        |
| OD-P14-02     | Extend `identity-service` or add a context beside it?               | **Closed** — `identity-service` owns all six as separated modules                                                                                                                                                                                                                                                                                                                                                         |
| OD-P14-03     | Does password fallback exist?                                       | **Closed** — yes, controlled; ceiling `substantial`; MFA always; disableable                                                                                                                                                                                                                                                                                                                                              |
| OD-P14-04     | Freshness and session-age values                                    | **Closed** — governed configuration with safe defaults                                                                                                                                                                                                                                                                                                                                                                    |
| OD-P14-05     | Is the session model canonical?                                     | **Closed** — service-level aggregate, not canon                                                                                                                                                                                                                                                                                                                                                                           |
| OD-P14-06     | Cross-origin bootstrap and handoff shape                            | **Closed** — per-workspace ceremony; `VotingHandoffArtifact` boundary fixed                                                                                                                                                                                                                                                                                                                                               |
| **OD-P14-07** | **Retention durations**                                             | **Open — pending legal confirmation.** PACK-09 owns retention schedules and a schedule is a legal determination, not this pack's to settle. **It does not block the reference implementation:** provisional schedules exist, every deletion prohibition is defined, deletion under hold refuses and unknown hold state fails closed. Confirming the durations changes configuration values, not the design (`AC-P14-115`) |
| OD-P14-08     | Which actions require attestation?                                  | **Closed** — none universally; governed privileged classes only                                                                                                                                                                                                                                                                                                                                                           |
| OD-P14-09     | Is SMS OTP permitted?                                               | **Closed** — not for authentication at all                                                                                                                                                                                                                                                                                                                                                                                |
| OD-P14-10     | Recovery assurance; eligibility reaching voting                     | **Closed** — resulting-confidence rule; the eligibility question assigned to PACK-15                                                                                                                                                                                                                                                                                                                                      |

## 11. Implementation dependencies

| Owner                   | What PACK-14 depends on and does **not** provide                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------------ |
| **PACK-09**             | Retention schedules, legal hold, destruction authorization                                       |
| **PACK-11**             | Governed documents, evidence bundles, custody chains for proofing and recovery evidence          |
| **PACK-12**             | Privileged grants, break-glass, separation of duties, audit-before-event                         |
| **PACK-13**             | The canonical envelope, outbox, projections and the data plane the identity records will live in |
| **PACK-15/16**          | The voting credential, eligibility, ballot, verification and tally                               |
| **PACK-17**             | Incident response and the operational side of takeover handling                                  |
| **FRONT-PACK**          | Every surface named in the frontend contract; PACK-14 builds none of them                        |
| **`FIR-FORM-001`**      | The canonical forms framework these fifteen forms will eventually be expressed in                |
| **`FIR-TRUST-001`**     | Electronic signatures — authentication is explicitly not one                                     |
| **`FIR-REPRESENT-001`** | Mandates and representation — a session identifies an actor, not a principal                     |
| **`FIR-INCLUSION-001`** | The assisted and offline channel framework                                                       |

## 12. Consistency checks performed

Mechanical checks over the 33 files in this archive:

| Check                                                                                                             | Result                                          |
| ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| No global ID preserved                                                                                            | PASS                                            |
| `account_id` never used as membership or login ID; `member_number` never a login ID                               | PASS                                            |
| Communication persona never an authentication subject                                                             | PASS                                            |
| No voting credential defined; handoff boundary only                                                               | PASS                                            |
| WS-03 shares no cookie, storage, session, analytics or telemetry                                                  | PASS                                            |
| No provider identifier becomes a global ID                                                                        | PASS                                            |
| authentication ≠ identity proofing ≠ membership eligibility ≠ authorization                                       | PASS                                            |
| Authentication is never an electronic signature                                                                   | PASS                                            |
| Support is never account-ownership authority                                                                      | PASS                                            |
| Recovery never bypasses assurance                                                                                 | PASS                                            |
| No generic `AUTH_ERROR` — the string appears twice, both times in its own prohibition                             | PASS                                            |
| No placeholder text anywhere                                                                                      | PASS                                            |
| Existing FRONT-00/FRONT-01 baseline inventoried, tokens extracted, no new design language                         | PASS                                            |
| Status banner on every document; no implementation, candidate, PASS, production or legal claim                    | PASS                                            |
| No code, tests, CI, version or canon change                                                                       | PASS — the repository working tree is untouched |
| `FIR-UX-003` … `FIR-UX-011` referenced, and no PACK-14 document defines a page order or navigation model          | PASS                                            |
| Register at its canonical path is the **cumulative** PACK-13 FINAL PASS register (`8d35a755…`), not standalone V5 | PASS                                            |
| All 140 cumulative entries preserved; `FIR-UX-011` added; 141 total, no duplicate identifier                      | PASS                                            |
| No PACK-13 status reopened — `FIR-ROADMAP-003`, `FIR-BASE-001`, §1.13 and section 21 unchanged                    | PASS                                            |

## 13. SHA-256 of every file in this archive

| File                                                                 | SHA-256                                                                                          |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `docs/adr/ADR-079-NO-GLOBAL-USER-IDENTITY.md`                        | `2d89a86c813de5c5c29ae95d8be3a6393fd2c09675df0634e20dd55d706a69fe`                               |
| `docs/adr/ADR-080-ACCOUNT-PERSON-MEMBERSHIP-SEPARATION.md`           | `ea29b5fb6876642cb693f57a3bce932024afbbc546747d23ae03a99e2da665fb`                               |
| `docs/adr/ADR-081-PASSKEY-FIRST-AUTHENTICATION.md`                   | `7dd81f97603838e432a74e4710e1ccaeed52abaf08b2b5b9092bd0e36fbd11bd`                               |
| `docs/adr/ADR-082-AUTHENTICATION-ASSURANCE-AND-STEP-UP.md`           | `01b668dcea7cd2b5db5bc0b1edf6bd899be305564f2866513af47d8e87b60e29`                               |
| `docs/adr/ADR-083-SESSION-SECURITY-AND-CROSS-WORKSPACE-ISOLATION.md` | `d247a67e3d54057928930f50573bc96f218be0e54d8e58c529856eb9ce552dd9`                               |
| `docs/adr/ADR-084-ACCOUNT-LIFECYCLE-AND-CREDENTIAL-GOVERNANCE.md`    | `cad2ede26ab337a3b44f764a1d195702f8097e04bbdc52236f71f70d2930c001`                               |
| `docs/adr/ADR-085-ACCOUNT-RECOVERY-AND-TAKEOVER-PROTECTION.md`       | `07499968294063e1a49337b6d0ab748cfcdbf19acbad405fc759d1562b42fa05`                               |
| `docs/adr/ADR-086-IDENTITY-PROOFING-BOUNDARY.md`                     | `de7e37c893c7d78417d45563375fb4652d5501a3fea84ddd55987bb6cfb4a039`                               |
| `docs/adr/ADR-087-PRIVILEGED-IDENTITY-ADMINISTRATION.md`             | `07a0c78c1c9e83f6c2483bf774bc56ed1937feb4ae5bc1e2215c69b459db6821`                               |
| `docs/adr/ADR-088-VOTING-HANDOFF-IDENTITY-SEPARATION.md`             | `7c00ff30dff09015c6902cd4f3e30a67dfaa5040113bc80238355ebb1984946b`                               |
| `docs/packs/PACK-14/PACK-14-ACCEPTANCE-MATRIX.md`                    | `2f79cc1d5cfe5fb5aa73eb7840a76f241d6cc3a856116f6f0a95cc0824db980f`                               |
| `docs/packs/PACK-14/PACK-14-ASSURANCE-LEVEL-MATRIX.md`               | `8cc987cea33e991a5f454e7d3f4bb94cc47359330bc8f0d1c34a90facb24bb73`                               |
| `docs/packs/PACK-14/PACK-14-ATTACHMENT-MATRIX.md`                    | `29f4fb77af34b673ac7d20c033c6bf74910687740d50310149a6b090a1b494ab`                               |
| `docs/packs/PACK-14/PACK-14-AUTHENTICATION-METHOD-MATRIX.md`         | `317a6a57ab15e71f7d3e335414f71e8cf106b6f3665a100b5607bc827f06b7dd`                               |
| `docs/packs/PACK-14/PACK-14-CANON-ASSESSMENT.md`                     | `c2623507d162797396f88dc2785192dfc9d3980d6b1418c5777ad5b3c94cbc7f`                               |
| `docs/packs/PACK-14/PACK-14-CONTENT-CATALOGUE-DE.md`                 | `5d7e8a69b238b43c7890b1fa5fd1100839c0d389e7d2b588443f5123506c860c`                               |
| `docs/packs/PACK-14/PACK-14-CROSS-WORKSPACE-SESSION-MATRIX.md`       | `c7731e015fb606e284ae87adf7a7b0f9ac5dfc5cd164430c7204be275ab173f7`                               |
| `docs/packs/PACK-14/PACK-14-EVENT-CATALOG.md`                        | `481fa30a8071b92ad3bf1b2c8d6bfac62a0ec667916cb46dc46c094327e20e7c`                               |
| `docs/packs/PACK-14/PACK-14-FIELD-CATALOGUE.md`                      | `5de067100fd65aedbbf530a2bae651644f812348fcf431bd15d395a6ab5f9a03`                               |
| `docs/packs/PACK-14/PACK-14-FIR-COVERAGE-MATRIX.md`                  | `50edeed95e166d9012ed48131c32c65a8eb82e648cfb4387d99e8632c992df35`                               |
| `docs/packs/PACK-14/PACK-14-FORM-INVENTORY.md`                       | `ccd75c7c8dbda9197039e6c0abd8d9d94dec663e0c18b2478337a75c2568ee83`                               |
| `docs/packs/PACK-14/PACK-14-IDENTITY-PROOFING-MATRIX.md`             | `6d2bd6ef547ef19ca99f7cd262332fa6ffd6405bb50f4595ee75783a377bb11e`                               |
| `docs/packs/PACK-14/PACK-14-IDENTITY-SEPARATION-MATRIX.md`           | `3c540a3324b0370e15ef6d2992b4a3a4b992e6974238661aa47b4861bb379eb2`                               |
| `docs/packs/PACK-14/PACK-14-PRIVACY-RETENTION-MATRIX.md`             | `1eda9782e27dc4f7742624770d8806a397067f2a9c46fcd184b3452a9ef71588`                               |
| `docs/packs/PACK-14/PACK-14-REASON-CODE-CATALOG.md`                  | `2ac7c469d447a8d81eb4e6d956bd15c487ac75e7f1ff090d70fa58300da34440`                               |
| `docs/packs/PACK-14/PACK-14-RECOVERY-CONTROL-MATRIX.md`              | `6ba597ac0cbd9f7fecf3cd0fa6bbbfccc4366c8dd531ed61ed87eca861110562`                               |
| `docs/packs/PACK-14/PACK-14-RENDITION-SPECIFICATION.md`              | `6942fe21be9ec246835305be8659fae5e2dae7a9ed2483fb7a9b8873cf82c3e4`                               |
| `docs/packs/PACK-14/PACK-14-SESSION-SECURITY-MATRIX.md`              | `377fcdf42979596c1750fd99de55ef2f1b5f56046e2e50118d2cc6d906f2ad04`                               |
| `docs/packs/PACK-14/PACK-14-SPECIFICATION.md`                        | `1f789142ddf51e0918fad9aefb0d85fada4308c1474d47377a1cdc6489b25e6a`                               |
| `docs/packs/PACK-14/PACK-14-THREAT-MODEL.md`                         | `2ac296339c9a9bc0f94a55082e8a607a4f5e0b834b0ca69ff07b3380a6591f79`                               |
| `docs/packs/PACK-14/PACK-14-WORKFLOW-MATRIX.md`                      | `55fdaa41c34e6718608b442b64517702a354618420a3da29a371c23fb1fa9e0e`                               |
| `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`         | `98487330d701a9d02a8431a481ca4ef7dc81fe4360441b2d7811659d19668a34`                               |
| `docs/handover/PACK-14-SPEC-ADR-REPORT.md`                           | _self-referential — a file cannot contain its own digest; compute it from the delivered archive_ |

## 14. Archive digest

The SHA-256 of the delivered archive is reported in the delivery message
accompanying it, and is deliberately not printed here: a file cannot
contain the digest of the archive that contains it.

```bash
sha256sum EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_SPEC_ADR.zip
```

---

## 15. What this round is not

It is not an implementation, a candidate or a PASS. The architecture
correction resolved decisions; it wrote no code. No authentication service
exists. No identity is verified. No session is issued. No account
can be recovered, because nothing has been built. It is not production
readiness, legal activation, a compliance statement, a procurement decision
or a provider commitment: no IAM, passkey provider, email or SMS provider,
or eID scheme is selected.

**Do not proceed to an implementation candidate without a separate task.**
