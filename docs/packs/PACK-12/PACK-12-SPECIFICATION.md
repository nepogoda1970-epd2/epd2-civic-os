# PACK-12 — Privileged Administration, Search & Data Export Security

**Round type:** specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**

> **Status note added by the PACK-12 implementation candidate round
> (2026-07-29).** The "specification-only / not implemented" statement
> above describes the *specification round* that produced this document
> and is preserved as the historical record. It is no longer the state of
> the repository: `services/privileged-access-service` now implements this
> specification as an **implementation candidate** at repository version
> `0.12.0`.
>
> **LOCAL VERIFICATION INCOMPLETE / EXTERNAL CI PENDING / NOT FINAL PASS.**
> Nothing here is claimed as verified, passed, or production-ready. See
> `docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md` section 5.


**Target version:** `0.12.0` — a target, not a setting. This round changes
no version. `REPOSITORY_VERSION` remains `0.11.0` and `CANON_VERSION`
remains `0.8.0`.

**Baseline:** `EPD2_PACK-11_GOVERNED_DOCUMENTS_EVIDENCE_0.11.0_FINAL_PASS.zip`
(PACK-01 through PACK-11: FINAL PASS).

**Register entry:** `FIR-ROADMAP-002`.

**Architecture gaps addressed:** `AGR-23` (privileged administration),
`AGR-24` (search, export and DLP by purpose and record class), and
foundation for `AGR-20` (statistical disclosure control).

---

## 0. How to read this document

Normative statements use **MUST**, **MUST NOT** and **SHOULD** in the
RFC-2119 sense and nowhere else. A sentence without one of those words is
explanation, not a requirement.

Every normative statement carries an identifier of the form
`P12-<AREA>-NNN`. The areas are `ROLE`, `PAM`, `BG`, `SES`, `SRCH`,
`HCD`, `EXP`, `DLP`, `SDC`, `ORG`, `EVT`, `RSN`, `FE`. Acceptance
criteria in `PACK-12-ACCEPTANCE-MATRIX.md` reference these identifiers;
threats in `PACK-12-THREAT-MODEL.md` reference them as their preventive
and detective controls.

### 0.1 Reconciliation basis

This specification has been reconciled against:

- `EPD2 Architecture Domain Framework 0.8.2 CORRECTED`;
- `EPD2 Target Frontend Architecture 0.8.2 CORRECTED`;
- canon `0.8.0` (`docs/canonical/TZ-00-domain-event-canon.md`);
- `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`;
- the accepted ADRs of PACK-01 through PACK-11.

The reconciliation resolved three defects in the first draft, each now
corrected and normative:

1. **Role classification.** System Administrator and Security
   Administrator are existing institutional roles in the Architecture
   Framework, not new operational roles. Section 3.1 and
   `PACK-12-ROLE-SEPARATION-MATRIX.md` section 1 now separate the two
   institutional roles PACK-12 consumes from the nine operational
   assignments it introduces.
2. **Data classification.** The framework's canonical classification
   values are authoritative and are not replaced by a simplified
   four-level scheme. `PACK-12-DATA-SEARCH-EXPORT-MATRIX.md` section 2
   now carries the normative mapping from canonical classification to a
   derived PACK-12 enforcement tier, with the source classification
   governing wherever the two differ.
3. **Voting material.** The blanket prohibition on "tallies" was too
   broad. Ballot-level material and intermediate or non-certified tally
   material remain absolutely prohibited; a final **certified** result
   released through the authoritative voting and result-certification
   domain is permitted and is not PACK-12's to own. See section 8.1.

`OD-P12-01` is closed by this reconciliation.

---

## 1. Purpose and position

PACK-12 defines the architecture and normative contracts for three
cross-cutting security domains that no earlier pack owns:

1. **Privileged Administration** — who may hold administrative power,
   how it is granted, bounded, evidenced, reviewed and revoked.
2. **Authorization-aware Search** — how a participant finds records
   without search becoming a second, weaker authorization path.
3. **Governed Data Export and DLP** — how data leaves the platform as a
   governed, approved, expiring, revocable object rather than as a
   download.

These three are one pack because they share one failure mode: each is a
plausible-looking way to obtain data that the ordinary authorization path
would refuse. A privileged role that can read anything, a search index
that answers from a stale ACL, and an export that quietly widens a read
permission into a bulk extraction are the same defect wearing three
different costumes. Splitting them across packs would let each one's
specification assume the other two had handled it.

### 1.1 What PACK-12 is not

PACK-12 is a **specification and ADR round**. It introduces no service,
no module, no schema file, no reason-code registry file, no event
implementation, no test and no frontend. `services/` is untouched. The
implementation round is a separate, later, separately-gated task and is
not authorised by this document.

Nothing in this document asserts production readiness, legal validity,
legal activation, regulatory compliance, or that any control described
here has been built or verified.

---

## 2. Relationship to earlier packs

PACK-12 depends on PACK-08, PACK-09, PACK-10 and PACK-11 and MUST NOT
break their stable interfaces.

| Pack        | What PACK-12 consumes                                                                                                                                                          | What PACK-12 MUST NOT do                                                                      |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| **PACK-02** | `audit-core`'s append-only hash-chained `AuditEvent`; the canonical event envelope (canon 21)                                                                                  | Write a second audit log; weaken or bypass the chain                                          |
| **PACK-08** | `OrganizationalAuthority`, `RoleAssignment`, `role_code` as an open string (19e.15), the pairwise incompatibility baseline (19e.16), the six cross-scope access modes (19e.12) | Mint its own organizational authority; reimplement scope resolution                           |
| **PACK-09** | `RecordClassRef`, `HoldRef`, `RetentionPolicy`, `LegalHold`, `DisposalEligibility`, procedural cases                                                                           | Re-decide retention, disposal or hold state; duplicate records governance                     |
| **PACK-10** | Finance record and report references; the finance separation-of-duties model as precedent                                                                                      | Re-decide any finance fact; export finance material outside finance's own disclosure controls |
| **PACK-11** | `DocumentRef`, `DocumentVersionRef`, `EvidenceRef`, `EvidenceBundleRef`, `PublicationRenditionRef`, the governed signature and admissibility determinations, sealed bundles    | Hold document bytes; re-assert authenticity, signature, admissibility or publishability       |

`P12-ORG-001` PACK-12 MUST consume every foreign domain exclusively
through the typed references those packs publish, and MUST NOT read
another service's storage directly.

`P12-ORG-002` PACK-12 MUST NOT introduce a reason code, event name or
entity that duplicates a concept an earlier pack already owns. Where a
refusal is really PACK-09's or PACK-11's, PACK-12 MUST surface that
pack's own reason code rather than shadowing it with a `PRIVILEGE_*`,
`SEARCH_*` or `EXPORT_*` synonym.

---

## 3. Privileged administration — roles

### 3.1 Two kinds of authority

PACK-12 works with **two existing institutional roles** and introduces
**nine privileged operational assignments**. The distinction is
normative; `PACK-12-ROLE-SEPARATION-MATRIX.md` section 1 is the full
statement.

**Existing institutional roles — consumed, not defined:** System
Administrator and Security Administrator. Both are already institutional
roles in the Architecture Framework. PACK-12 preserves their
institutional semantics and their existing incompatibilities unchanged
and adds only boundary obligations (`P12-ROLE-003`, `P12-ROLE-004`,
`P12-ROLE-014`, `P12-ROLE-015`).

**PACK-12 privileged operational assignments — nine, introduced here:**

| `role_code`                              | Holds                                                                 | Explicitly does not hold                                            |
| ---------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `iam_administrator`                      | Identity lifecycle, credential binding, role assignment mechanics     | Self-grant of privileged domain access; approval of own assignments |
| `audit_custodian`                        | Audit availability, retention, chain verification, evidence sealing   | Modification or deletion of audit records; domain decisions         |
| `domain_administrator`                   | Administration of ONE named domain within ONE organizational scope    | Any other domain; any other scope; platform-wide administration     |
| `data_owner`                             | Authority over a record class in a scope; export authorization for it | Authority over classes they do not own; privileged access grants    |
| `export_approver`                        | Approval or refusal of a specific export request                      | Requesting the export they approve; DLP policy authorship           |
| `dlp_security_officer`                   | DLP policy authorship, DLP assessment review, forbidden-data findings | Approval of the exports they assess; domain decisions               |
| `independent_privileged_access_reviewer` | Periodic and post-access review of grants and sessions                | Any grant, any approval, any operational privilege                  |
| `break_glass_approver`                   | The second control on a break-glass activation                        | Activating the break-glass they approve; suppressing notification   |
| `disclosure_control_reviewer`            | Small-cohort, cumulative-release and differencing review; exceptions  | Requesting the release they review; raw-data operational access     |

The nine are registered through canon 19e.15's open `role_code` list by
`ADR-061-pack-12-privileged-role-separation.md`. PACK-12 adds no new
canonically-named institutional role to canon 19e.16's seven-role list.

### 3.2 Hard separation rules

`P12-ROLE-001` There MUST be no universal administrator. No `role_code`,
no combination of `role_code` values, and no configuration MAY confer
unrestricted access spanning all domains, all scopes and all operations
(register `FIR-INV-014`).

`P12-ROLE-002` Holding one administrative role MUST NOT confer the
authority of another. Authority is per-role, per-scope, per-purpose,
per-operation, and is never inherited between administrative roles.

`P12-ROLE-003` `system_administrator` MUST NOT be granted read access to
domain content as a consequence of administering the infrastructure that
stores it. Infrastructure authority and content authority are separate
grants with separate justifications.

`P12-ROLE-004` `security_administrator` MUST NOT be able to take a domain
decision. Security administration configures the rules; it does not
decide cases, approve documents, authorise payments or publish.

`P12-ROLE-005` `iam_administrator` MUST NOT be able to grant themselves
privileged domain access. Any assignment naming the requesting IAM
administrator as subject MUST require a distinct approver holding an
appropriate role.

`P12-ROLE-006` `audit_custodian` MUST NOT be able to modify or delete an
audit record within their own custody. The custodian's power is
availability, verification and sealing; it is never mutation.

`P12-ROLE-007` `domain_administrator` MUST be bound to exactly one named
domain and one organizational scope per grant.

`P12-ROLE-008` Security administration MUST be separated from system
administration (register `FIR-INV-008`).

`P12-ROLE-009` Privileged access MUST be separated from ordinary
application authorization. An ordinary product role MUST NOT become a
privileged role by accumulation, configuration default, or convenience.

`P12-ROLE-010` An election result, an appointment, a mandate or a
management position MUST NOT provision privileged access automatically.
Privileged access is always a separate, explicit, justified grant.

`P12-ROLE-011` Every privilege grant MUST be explicit, scoped,
time-bound and independently reviewable.

`P12-ROLE-012` PACK-12 MUST extend PACK-08's pairwise role-incompatibility
baseline with the pairs in `PACK-12-ROLE-SEPARATION-MATRIX.md`, and MUST
NOT remove any existing pair. Canon 19e.16's own closing rule permits
making the baseline stricter and forbids relaxing it.

`P12-ROLE-013` Role incompatibility MUST be evaluated both at assignment
time and again at the moment of the act, over the roles the acting
subject actually holds in that scope. PACK-10's `assert_authorized` is
the precedent.

`P12-ROLE-014` PACK-12 MUST NOT redefine, rename, narrow or widen the
institutional semantics of System Administrator or Security
Administrator.

`P12-ROLE-015` The existing institutional incompatibility between those
two roles is preserved unchanged; PACK-12 depends on it rather than
creating it.

`P12-ROLE-016` An operational assignment MUST NOT replace or stand in
place of an institutional role.

`P12-ROLE-017` An operational assignment MUST be conferred only through
governed authority resolved via the authorization port.

`P12-ROLE-018` Every operational assignment MUST be scope-bound,
purpose-bound and effective-dated.

`P12-ROLE-019` An operational assignment MUST NOT extend, widen or
supplement canonical institutional authority.

`P12-ROLE-020` Existing institutional incompatibilities MUST be preserved
in full; PACK-12's additions are cumulative, never substitutional.

`P12-ROLE-021` An operational assignment MUST NOT be used to obtain, by
composition or by sequence, an authority the Institutional Role Matrix
would refuse.

---

## 4. Privileged access management

### 4.1 Lifecycle

The governed lifecycle of a `PrivilegedAccessGrant` is:

```text
requested
→ under_evaluation        (separation-of-duties and policy evaluation)
→ approved | denied
→ activated               (grant becomes usable; session may start)
→ active
→ expired | revoked
→ under_post_access_review
→ review_completed
```

`P12-PAM-001` A privileged-access request MUST carry, at minimum: the
requesting actor reference, a written justification, a declared
`purpose`, the target system or domain, the requested operations, the
organizational scope, the data classes, the requested duration, and a
risk classification.

`P12-PAM-002` Every grant MUST be simultaneously purpose-scoped,
resource-scoped, operation-scoped, organization-scoped, time-bound,
attributable, independently reviewable, revocable and auditable. A grant
missing any one of these nine properties MUST NOT be issuable.

`P12-PAM-003` A permanent standing superuser MUST NOT be designed as a
normal operating mode. Where an emergency genuinely requires wider
authority, the governed path is break-glass (section 5), not a standing
grant.

`P12-PAM-004` The requester MUST NOT be an approver of their own request,
directly or through a role they also hold.

`P12-PAM-005` Separation-of-duties evaluation MUST run before approval
and MUST be re-evaluated at activation. A subject whose role set changed
between approval and activation MUST be re-evaluated rather than
activated on the stale evaluation.

`P12-PAM-006` A grant MUST expire automatically at its recorded end
instant. Expiry MUST NOT depend on a human remembering to revoke it, and
MUST NOT be extendable in place. Continuation is a new request with a new
decision.

`P12-PAM-007` Revocation MUST be possible at any point while a grant is
active, MUST take effect on subsequent authorization checks immediately,
and MUST be reason-coded.

`P12-PAM-008` Grants MUST be subject to periodic review by an
`independent_privileged_access_reviewer` who holds no operational
privilege over the reviewed scope.

`P12-PAM-009` Dormant grants — approved or activated but unused for a
policy-defined interval — MUST be surfaced for review and SHOULD be
revoked by default.

`P12-PAM-010` Authorization MUST be re-checked at every privileged
operation against the grant's current state. A started session MUST NOT
carry authority past its grant's expiry or revocation.

### 4.2 Entities

`PrivilegedAccessRequest`, `PrivilegedAccessDecision`,
`PrivilegedAccessGrant`, `PrivilegedRoleBinding`, `AccessRiskClassification`,
`SeparationOfDutiesEvaluation`, `PrivilegedAccessReview`,
`PostAccessReview`.

Each is a governed object with an immutable history. `PACK-12-EVENT-CATALOG.md`
gives the event family; `PACK-12-REASON-CODE-CATALOG.md` gives the
refusals.

---

## 5. Break-glass

`P12-BG-001` Break-glass MUST be a separate workflow from ordinary
privileged access, with its own request object, its own decision and its
own event family. It MUST NOT be reachable as a parameter, flag or
escalation of the ordinary approval workflow.

`P12-BG-002` Activation MUST require a documented emergency condition. An
activation whose emergency condition is absent or unstated MUST be
refused with `PRIVILEGE_BREAK_GLASS_CONDITION_ABSENT`.

`P12-BG-003` Break-glass MUST be dual-controlled: the activating actor and
a distinct `break_glass_approver`. Missing dual control MUST refuse with
`PRIVILEGE_BREAK_GLASS_DUAL_CONTROL_MISSING`.

`P12-BG-004` Break-glass MUST be time-bound with a short policy-defined
maximum, MUST be narrowly scoped, and MUST expire automatically.

`P12-BG-005` Every break-glass activation MUST be reason-coded and MUST
produce session evidence (section 6).

`P12-BG-006` An out-of-band notification MUST be dispatched to an
independent recipient on activation. The dispatch MUST be recorded as an
event with its own evidence.

`P12-BG-007` The notification MUST NOT be suppressible, delayable or
redirectable by the actor who activated the break-glass, nor by any
subject that actor can direct.

`P12-BG-008` The transport and provider for out-of-band notification are
**not** decided by PACK-12. They are governed by the later gateway and
incident packs. What PACK-12 fixes now is that the notification event and
its evidence are mandatory, and that a break-glass activation whose
notification could not be dispatched MUST be recorded as such and
escalated — never silently completed.

`P12-BG-009` Break-glass MUST NOT suspend, weaken or override any hard
invariant.

`P12-BG-010` Break-glass MUST NOT grant access to ballot content, vote
envelopes, tallies or any voting secret, under any emergency condition.

`P12-BG-011` Break-glass MUST NOT disable, bypass, pause or reduce audit.

`P12-BG-012` A justification recorded at activation MUST NOT be editable
afterwards. Later clarification is an appended record, never a rewrite.

`P12-BG-013` Renewal MUST be a new decision with new dual control. There
is no automatic extension.

`P12-BG-014` Every break-glass use MUST undergo independent review after
the fact, by a reviewer who was neither the activator nor the approver.

---

## 6. Privileged session evidence

`P12-SES-001` A privileged session MUST produce session evidence
containing at minimum: session identifier; actor reference; effective
privileged role; source grant reference; purpose; target system; target
domain; organization scope; permitted operations; start and end instants;
governed operation summaries; accessed resource references; any search or
export actions triggered within the session; approval references;
break-glass marker; integrity or hash reference; evidence bundle
reference; review status.

`P12-SES-002` Session evidence MUST NOT contain secrets, plaintext
credentials, private key material, or full sensitive payloads.

`P12-SES-003` Session evidence MUST record _references to_ accessed
resources, not copies of them. The audit subsystem MUST NOT become an
unbounded archive of user content.

`P12-SES-004` Session evidence MUST be sealed at session end with a
tamper-evident integrity reference, and the sealing MUST be its own
event.

`P12-SES-005` Session evidence MUST reuse PACK-11's evidence-bundle model
by reference rather than defining a parallel evidence store.

`P12-SES-006` Session evidence MUST be readable by an
`independent_privileged_access_reviewer` and by an `audit_custodian`
without either being able to alter it.

`P12-SES-007` Tamper evidence is not tamper resistance. PACK-12 MUST NOT
claim that sealed session evidence cannot be altered by an actor with
sufficient infrastructure access; it claims only that alteration is
detectable. Cryptographic anchoring beyond the hash chain is out of scope
and depends on the later key-management work.

---

## 7. Search architecture

### 7.1 Modes

`P12-SRCH-001` PACK-12 MUST NOT define a global unrestricted search.

`P12-SRCH-002` PACK-12 MUST define at least two modes: **general
authorized search** and **scoped/domain search**. A third mode,
**privileged investigative search**, MAY be defined, and if defined MUST
be a purpose-scoped governed operation with its own grant, its own
approval and its own session evidence — never an ambient capability of an
administrative role.

### 7.2 Authorization rules

`P12-SRCH-003` Search MUST NOT expand source authorization. A participant
MUST be able to find only what they would be permitted to open directly.

`P12-SRCH-004` Authorization MUST be enforced at indexing time **and**
again at query time and at result retrieval. Index-time enforcement alone
is insufficient.

`P12-SRCH-005` Stale authorization MUST NOT preserve access through the
index. Where the index's authorization view may lag the source, the query
path MUST re-resolve authorization against the source's current state
before returning a result.

`P12-SRCH-006` Snippets, highlights and any derived excerpt MUST be
subject to the same restrictions as the source record.

`P12-SRCH-007` Result counts MUST NOT reveal the existence of records the
requester may not access. A count MUST be computed over the authorized
result set only.

`P12-SRCH-008` Autocomplete, facets, aggregations, suggestions and
"did you mean" MUST NOT disclose restricted values, restricted terms or
the existence of restricted records.

`P12-SRCH-009` Caches MUST NOT mix security contexts. A cache key MUST
include the effective authorization context, and a cache entry MUST NOT
be served across subjects, scopes or purposes.

`P12-SRCH-010` Organization scope MUST be a mandatory query parameter.
An undeterminable scope MUST deny.

`P12-SRCH-011` Purpose MAY further restrict results and MUST NOT widen
them.

`P12-SRCH-012` Deleted, expired and access-revoked records MUST cease to
be retrievable through search.

`P12-SRCH-013` A legal hold MAY preserve a record from disposal but MUST
NOT widen access to it, and MUST NOT make it searchable to anyone who
could not otherwise reach it.

`P12-SRCH-014` The search index MUST NOT be an authoritative source. A
search result MUST NOT create legal effect.

`P12-SRCH-015` The search index MUST NOT become a route around retention
or deletion policy. Index removal MUST be evidenced.

### 7.3 Entities

`IndexPolicy`, `IndexFieldPolicy`, `SearchScope`, `SearchPurpose`,
`QueryRequest`, `QueryDecision`, `QueryAudit`, `SearchResultReference`,
`IndexProjectionReference`, `ReindexRequest`, `IndexRemovalEvidence`.

`P12-SRCH-016` `SearchResultReference` MUST carry a reference to the
source record and MUST NOT carry the record's content beyond a policy-
bounded snippet that itself passed the section 7.2 checks.

---

## 8. Classification, highly confidential domains and voting material

### 8.0 Source classification is authoritative

`P12-CLS-001` The canonical or source classification of a record is
authoritative. PACK-12 MUST NOT change it, lower it, override a
domain-specific restriction, or substitute for an authoritative
record-class policy.

`P12-CLS-002` A PACK-12 **enforcement tier** is a derived policy
abstraction only, carrying no authority of its own. Where tier and source
classification disagree, the source classification governs.

`P12-CLS-005` An unmapped source classification MUST default to the
most restrictive non-prohibited tier and fail closed pending an explicit
mapping decision.

The normative mapping from canonical classification to enforcement tier —
covering Public / approved, Public authoritative, Internal, Confidential
/ regulated, Confidential case metadata, Derived decision, Highly
confidential and the absolutely-excluded category — is
`PACK-12-DATA-SEARCH-EXPORT-MATRIX.md` section 2.

### 8.1 Voting material — two distinct categories

`P12-VOTE-001` The following MUST NEVER be reachable through any PACK-12
search or export path, under any purpose, role, approval or emergency
condition: ballot content; individual vote selections; vote envelopes;
eligibility- or credential-to-ballot linkage; voter-to-choice linkage;
cryptographic voting secrets; intermediate tally; partial tally;
non-certified tally material; and raw tally inputs from which individual
choices could be reconstructed.

`P12-VOTE-002` That prohibition MUST be structural rather than
configurational: PACK-12 defines no reference type capable of pointing at
any of the above.

`P12-VOTE-003` `P12-BG-010` extends the prohibition to break-glass; no
emergency condition reaches any of it.

`P12-VOTE-004` A final **certified** result MAY be published or
transmitted, and PACK-12 MUST NOT be read as forbidding it. It is
permitted only when it flows through the authoritative voting and
result-certification domain; the vote is formally closed; certification
has occurred; release is through an approved publication rendition; it
carries no ballot-level data; it carries no correlation identifiers; it
is not obtained through privileged administrative search; it is not
obtained through any PACK-12 raw export path; and it carries evidence
references to the certification and publication decisions.

`P12-VOTE-005` PACK-12 MAY audit **the fact** that a governed publication
occurred. PACK-12 MUST NOT own voting-result semantics, MUST NOT certify,
MUST NOT decide closure, and MUST NOT be a publication path of its own.

`P12-VOTE-006` Until certification and closure have occurred, result
material remains under `P12-VOTE-001`.

### 8.2 Highly confidential domains excluded from the general index

`P12-HCD-001` The following MUST be excluded from the general search
index by default:

- ballot-level and intermediate-tally material (§8.1, absolute);
- whistleblower reporter identity and protected submissions;
- cryptographic credentials and secret material;
- highly sensitive legal and disciplinary case content;
- medical or comparable special-category data, should such domains exist;
- protected citizen correspondence;
- raw privileged-session secrets;
- sealed evidence;
- legally restricted finance and compliance material;
- any record marked restricted by an authoritative record-class policy.

`P12-HCD-002` Whistleblower reporter identity and protected submissions
MUST be excluded from ordinary search, administrative search, HR access
and management access alike.

`P12-HCD-003` Ballot-level and intermediate-tally material MUST NOT be
indexed for administrative search under any configuration.

`P12-HCD-004` Secrets, credentials and cryptographic key material MUST
NOT be indexed.

`P12-HCD-005` This list is a floor, not a ceiling. Where a specific
domain imposes a stricter rule, that rule governs. PACK-12 MUST NOT be
read as permitting anything a domain forbids merely because this list did
not name it.

---

## 9. Governed data export

### 9.1 Export is not download

`P12-EXP-001` Export MUST be modelled as a governed object with a
lifecycle, not as a download action.

```text
requested
→ dlp_assessment
→ disclosure_assessment
→ approved | denied
→ artifact_generated
→ delivered
→ accessed*                 (repeatable, each access audited)
→ expired | revoked
→ destruction_attested      (where the recipient obligation requires it)
```

### 9.2 Entities

`ExportRequest`, `ExportPurpose`, `ExportScope`, `DatasetManifest`,
`DatasetItemReference`, `Recipient`, `RecipientObligation`,
`ExportApproval`, `ExportDecision`, `ExportArtifact`, `ExportDelivery`,
`ExportExpiry`, `ExportRevocation`, `ExportAccessEvent`,
`ExportDestructionAttestation`, `DLPAssessment`, `DisclosureRiskAssessment`.

### 9.3 Required request content

`P12-EXP-002` An export request MUST carry: requesting actor; purpose;
legal or organizational basis reference where required; source domains;
record classes; filters and time range; organization scope; requested
fields; requested format; recipient; recipient category; transfer
channel; retention and expiry; downstream-use restrictions; re-sharing
restrictions; required redaction; required pseudonymization; watermark
requirements; approval requirements; disclosure-risk assessment; and the
export manifest.

### 9.4 Authorization rules

`P12-EXP-003` Every item listed in `P12-VOTE-001` — ballot-level
material, intermediate, partial and non-certified tally material — MUST
NOT be exportable by any path, purpose, role or emergency condition. A
final certified result is **not** in this prohibition: it is released by
the authoritative voting and result-certification domain under
`P12-VOTE-004`, never through a PACK-12 export path.

`P12-EXP-004` Search permission MUST NOT imply export permission.

`P12-EXP-005` Read permission MUST NOT imply bulk-export permission.

`P12-EXP-006` An administrative privilege MUST NOT imply export
authority. Export authority derives from the `data_owner` for the record
class in scope, plus an `export_approver`, and never from the fact that
someone administers the system.

`P12-EXP-007` Raw database access MUST NOT be an acceptable substitute
for governed export, and MUST be treated as a control failure where it
occurs.

`P12-EXP-008` An export MUST include only explicitly permitted fields.
Denied fields MUST be excluded **before** the artifact is generated, not
filtered at delivery or hidden in presentation.

`P12-EXP-009` The manifest MUST describe the artifact's composition
without unnecessarily disclosing sensitive content.

`P12-EXP-010` Every artifact MUST have an expiry.

`P12-EXP-011` Every access to an artifact MUST be audited.

`P12-EXP-012` An export MUST be revocable before expiry.

`P12-EXP-013` Revocation MUST NOT be described as physical deletion of a
copy the recipient already holds. It withdraws authorization and blocks
further platform-mediated access; it does not reach outside the platform.

`P12-EXP-014` Downstream obligations MUST be explicit on the export
object, not implied by context.

`P12-EXP-015` Re-sharing MUST require a separate basis unless the
recipient obligation explicitly permits it.

`P12-EXP-016` An export MUST inherit the applicable retention, legal-hold
and destruction obligations of its source records.

`P12-EXP-017` A legal hold MUST NOT be treated as authorization to
export.

`P12-EXP-018` Records revoked or deleted at source MUST NOT
automatically persist into new exports.

`P12-EXP-019` Every new export MUST be formed against the current
authorization and policy state. A prior approval MUST NOT authorise a
later regeneration.

`P12-EXP-020` An export artifact MUST NOT become an authoritative domain
record.

`P12-EXP-021` A generated file MUST be bound to an immutable manifest and
to evidence references.

`P12-EXP-022` The export lifecycle MUST emit tamper-evident events.

---

## 10. DLP controls

`P12-DLP-001` The following MUST be available as policy-level controls:
field suppression; field masking; redaction; pseudonymization;
aggregation; cohort threshold; recipient restrictions; watermarking;
expiry; download limits; transfer-channel restrictions; export size and
frequency limits; repeated-query and repeated-export detection;
unusual-volume review; forbidden-data detection; manual review triggers;
revocation; destruction confirmation.

`P12-DLP-002` A DLP assessment MUST complete before an export decision,
and its outcome MUST be recorded as an event.

`P12-DLP-003` A `dlp_security_officer` MUST NOT approve an export they
assessed. Assessment and approval are separate acts by separate subjects.

`P12-DLP-004` PACK-12 MUST NOT claim that watermarking, expiry or
revocation guarantees deletion or non-disclosure at an external
recipient. These are deterrent, attribution and containment controls.
Their limits MUST be stated wherever they are described to an operator.

`P12-DLP-005` Forbidden-data detection MUST fail closed: a detection the
system could not complete MUST block the export pending manual review,
never pass it.

---

## 11. Statistical disclosure control — foundation

PACK-12 defines the contract-level foundation for `AGR-20`. It does not
implement a production analytics engine, and the production data plane
remains PACK-13's.

`P12-SDC-001` Publication or export of small samples MUST require a
disclosure-risk assessment.

`P12-SDC-002` Privilege to access raw data MUST NOT imply authority to
publish or export it.

`P12-SDC-003` Repeated and differential queries MUST be accounted for
across time, not evaluated only per request.

`P12-SDC-004` Several individually permissible exports MAY together
create re-identification risk; cumulative release MUST be assessed.

`P12-SDC-005` A numeric threshold MUST NOT be the only protection.

`P12-SDC-006` Exceptions MUST be explicitly approved by a
`disclosure_control_reviewer` and MUST be audited.

`P12-SDC-007` Suppressed values MUST NOT be recoverable through totals,
facets, neighbouring cohorts or successive queries.

`P12-SDC-008` Query and release history MUST be available to the
`disclosure_control_reviewer`.

Entities: `CohortPolicy`, `DisclosureRule`, `DisclosureRiskAssessment`,
`ReleaseHistoryReference`, `SuppressionDecision`,
`DisclosureExceptionRequest`, `DisclosureExceptionDecision`.

---

## 12. Organizational isolation

`P12-ORG-003` Every privileged grant, search scope and export MUST carry
an organizational scope drawn from the PACK-08 model (Bund, Land, Kreis
and other governed organizational units).

`P12-ORG-004` A grant issued for one organization MUST NOT be effective
in another.

`P12-ORG-005` National system administration MUST NOT imply access to the
content of all organizations.

`P12-ORG-006` Cross-organizational search or export MUST require its own
scope and its own basis, resolved through PACK-08's six cross-scope
access modes and never inferred.

`P12-ORG-007` The `data_owner` and the approver MUST correspond to the
authoritative organizational responsibility for the record class in that
scope.

`P12-ORG-008` Shared infrastructure MUST NOT dissolve organizational
isolation. Co-tenancy is an implementation fact, not an authorization
fact.

---

## 13. Events

`P12-EVT-001` PACK-12 MUST define versioned event families for
privileged access, break-glass, search and export, as catalogued in
`PACK-12-EVENT-CATALOG.md`.

`P12-EVT-002` Events MUST use the canonical envelope of canon section 21
unchanged.

`P12-EVT-003` Event payloads MUST NOT contain plaintext secrets,
credentials, key material, ballot content, or full sensitive payloads.

`P12-EVT-004` Event names MUST follow the aggregate-prefix convention
canon section 20 uses throughout (`privileged_access.requested`, not
`pack12.privileged_access_requested`).

---

## 14. Reason codes

`P12-RSN-001` PACK-12 MUST define a governable reason-code taxonomy with
the prefixes `PRIVILEGE_`, `SEARCH_`, `EXPORT_` and `DISCLOSURE_`.

`P12-RSN-002` A single generic `FORBIDDEN` code MUST NOT be used in place
of the taxonomy. Every governed refusal MUST name what was refused and
why, at a granularity an operator and an auditor can act on.

`P12-RSN-003` Where a refusal genuinely belongs to an earlier pack,
PACK-12 MUST surface that pack's registered code rather than minting a
synonym.

The full catalogue is `PACK-12-REASON-CODE-CATALOG.md`.

---

## 15. Frontend boundary

PACK-12 is not a FRONT-PACK.

`P12-FE-001` PACK-12 MAY define only the governed administrative surfaces
needed by its own workflows: privileged-access request; grant approval
and rejection; active-grant review and revocation; break-glass
activation; break-glass independent review; privileged-session evidence
review; scoped search review; export request; export approval; DLP and
disclosure review; export status, expiry and revocation; query and export
audit view.

`P12-FE-002` These are security-administration surfaces. PACK-12 MUST NOT
be expanded into full frontend workspace development.

`P12-FE-003` The visual design system, complete navigation and production
frontend integration MUST remain with the relevant FRONT-PACK.

`P12-FE-004` Different administrative roles MUST NOT be given one
universal console. A universal console is `FIR-INV-014`'s prohibited
universal admin panel wearing a UI.

`P12-FE-005` The frontend MUST NOT be a security boundary. Backend
authorization MUST re-check every action independently of what the client
displayed or permitted.

`P12-FE-006` Sensitive data MUST NOT reach client logs, analytics or
shared telemetry.

`P12-FE-007` A privileged-session UI MUST NOT run on an ordinary shared
end-user session without a separate assurance contract.

`P12-FE-008` The final authentication and session architecture depends on
PACK-14 and MUST NOT be settled here.

---

## 16. Explicit exclusions

PACK-12 does not implement or fully specify, and MUST NOT be read as
providing: the production database platform; the schema registry and
contract-evolution runtime; the final external identity provider;
complete authentication and MFA; PKI, HSM or key management; the voting
unlinkability protocol; voting implementation; a full incident-response
platform; backup and recovery implementation; the complete communications
gateway; complete frontend workspaces; public transparency publication;
an external recipient portal; production DLP vendor integration; full
legal activation; party operational policy as legally approved policy;
or any unrelated product domain.

These MAY be referenced as dependencies. They MUST NOT be absorbed into
PACK-12.

---

## 17. Dependencies

| Dependency | What PACK-12 needs from it                                             | PACK-12 position                                                        |
| ---------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| PACK-13    | Production data plane; real index; durable event bus; schema registry  | PACK-12 specifies contracts; the runtime that carries them is PACK-13's |
| PACK-14    | Authentication, session assurance, external gateway, identity provider | PACK-12 assumes an authenticated actor reference; it does not mint one  |
| PACK-15/16 | Voting trust boundary and implementation                               | PACK-12 only forbids reaching voting material; it defines no voting     |
| PACK-17    | Incident response, out-of-band transport, resilience                   | PACK-12 mandates the notification event; the transport is PACK-17's     |
| FRONT-PACK | Workspace UX, design system, navigation                                | PACK-12 defines administrative surfaces only                            |

---

## 18. Open implementation decisions

| ID              | Decision                                                                                 |
| --------------- | ---------------------------------------------------------------------------------------- |
| ~~`OD-P12-01`~~ | **CLOSED** — reconciled against framework 0.8.2 CORRECTED; see section 0.1               |
| `OD-P12-02`     | Whether privileged investigative search is defined at all in the implementation round    |
| `OD-P12-03`     | Numeric values for break-glass maximum duration, dormancy interval and cohort thresholds |
| `OD-P12-04`     | Whether PACK-12 owns one service or three bounded contexts                               |
| ~~`OD-P12-05`~~ | **CLOSED** — ADRs renumbered `ADR-061`..`ADR-068` in this corrected package              |
| `OD-P12-06`     | Whether `QueryAudit` lives in `audit-core` or in the PACK-12 context                     |
| `OD-P12-07`     | Recipient-category taxonomy and which categories may ever receive special-category data  |
| `OD-P12-08`     | How cumulative-release accounting is bounded in time and storage                         |

---

## 19. Status

**PACK-12 SPECIFICATION + ADR — NOT IMPLEMENTED, NOT A CANDIDATE, NOT A PASS.**

No code was written. No existing file was changed. `REPOSITORY_VERSION`
remains `0.11.0`; `CANON_VERSION` remains `0.8.0`. Nothing in this
document asserts production readiness or legal activation.
