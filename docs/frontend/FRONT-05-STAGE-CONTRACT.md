# FRONT-05 STAGE CONTRACT — WS-04 Representative Workspace

Contract version `1.0.0` · schema `epd2.front05.stage-contract/1`

This document is the human-readable mirror of `FRONT-05-STAGE-CONTRACT.json`.
The JSON is the machine authority: `scripts/validate_front05.py` reads it and
derives its gates from it rather than from constants baked into the validator.
Both files are inside the digest-covered source set, so neither can be changed
without changing the source-tree digest that every evidence record is bound to.

## 1. What this package is, and is not

**Scope class.** BOUNDED WS-04 FRONTEND CANDIDATE

**Acceptance meaning.** Nothing is accepted by this package. It is a C1 candidate that records an implemented, isolated, mandate-scoped WS-04 frontend and the mechanically demonstrated absence of every prohibited capability for independent governed review.

**FRONT-05 is open only for this bounded C1 acceptance attempt.** The project
owner directive recorded in `FRONT-05-C1-GOVERNANCE-OPENING.json` permits a
sealed exact-byte candidate and independent review. Its internal state remains
`CANDIDATE_NOT_ACCEPTED`, and its highest self-assertion is
`PASS_FOR_INDEPENDENT_ACCEPTANCE`.

It claims none of the following:

- FRONT-05 accepted
- FRONT layer closed
- representative workspace production ready
- mandate register accepted
- case desk runtime accepted
- publication approval implemented
- legal activation complete
- BSI certified
- CC compliant
- EAL4
- SEC PASS
- final integration pass

## 2. Ratification

- Authored by: developer, as a separately reviewable artifact
- Ratified by: independent governance
- Status in this package: `PROPOSED_FOR_GOVERNED_RATIFICATION`

This contract is the authority the FRONT-05 validator reads. The candidate does not ratify it. Ratification remains conditional on independent exact-byte PASS and the post-run governance record.

## 3. Workspace boundary

- Workspace: `WS-04` — Mandate Holder Workspace
- Origin: `https://represent.epd.example`
- Route prefix: `/representative`
- Separately deployable: True
- May import the Member Workspace runtime: False
- May import the Voting Client runtime: False

### Open governance item: the route prefix

The accepted frontend policy record carries `/Mandate Holder` in its
route-prefix field, which is a display name rather than a path. The target
architecture gives `/representative`. This package uses `/representative` and records the
conflict for the accepting authority rather than silently choosing one and
presenting it as settled.

## 4. Routes

| Page | Route | Title | Authority required |
| --- | --- | --- | --- |
| `WS04-R01` | `/representative` | Übersicht | `mandate_member` |
| `WS04-R02` | `/representative/desk` | Bürgeranliegen | `mandate_staff_assigned` |
| `WS04-R03` | `/representative/desk/[caseId]` | Vorgang | `mandate_staff_assigned` |
| `WS04-R04` | `/representative/positions` | Positionen | `mandate_representative` |
| `WS04-R05` | `/representative/deviations` | Abweichungen | `mandate_representative` |
| `WS04-R06` | `/representative/declarations` | Erklärungen | `mandate_representative` |
| `WS04-R07` | `/representative/publication` | Veröffentlichungsvorschläge | `mandate_representative` |
| `WS04-R08` | `/representative/conflicts` | Zugriffsbeschränkungen | `mandate_member` |
| `WS04-R00` | `/` | Mandatsbereich | `none` |

No route creates authority. Reaching a route is never a decision; the server
decision does not exist yet, and the interface says so on every surface.

## 5. Roles

- Primary: `representative`, `mandate_staff`
- Secondary: `publication_reviewer`, `conflict_officer`
- Forbidden, in any form: `super_admin`, `representative_all`, `system_admin`, `global_admin`, `cross_mandate_operator`, `bund_all_access`, `debug_bypass`

## 6. Hard invariants

| ID | Class | Statement |
| --- | --- | --- |
| `INV-01` | `HARD` | No universal, cross-mandate or administrative mode exists, under any role, permission or debug flag. |
| `INV-02` | `HARD` | Every protected read and action binds to exactly one mandate scope, and no unbound form is expressible. |
| `INV-03` | `HARD` | WS-04 may propose a publication rendition and may never approve one. No approval state is reachable from any client state under any event. |
| `INV-04` | `HARD` | WS-04 holds no registry custody: no registry mutation operation exists. |
| `INV-05` | `HARD` | WS-04 takes no eligibility decision; it may only display one made elsewhere. |
| `INV-06` | `HARD_FREEZE` | WS-04 has no voting-domain access of any kind, for any role. |
| `INV-07` | `HARD` | Case content is never written to browser storage, a URL, the page title, a telemetry event or an error report. |
| `INV-08` | `HARD` | No authoritative decision is taken in the client; a rendered control is never an authorization. |
| `INV-09` | `HARD` | A refusal about a protected resource is non-disclosing: absent, out of scope and restricted are indistinguishable. |
| `INV-10` | `HARD` | An unreadable conflict register restricts rather than permits; unknown is never treated as cleared. |
| `INV-11` | `HARD` | No specification-level or unaccepted API path is treated as an executable runtime route, and no network request is issued from the production adapter. |
| `INV-12` | `HARD` | No success language may precede an authoritative server outcome, and a blocked compliance submission must state that the obligation remains open. |
| `INV-13` | `HARD` | The inherited FRONT-00/FRONT-01 visual baseline is immutable without a Design Change Decision. |
| `INV-14` | `HARD` | Inherited accepted evidence and documents are byte-identical to the accepted bytes they came from. |
| `INV-15` | `HARD` | A recorded PASS is bound to the source tree that produced it; stale evidence must cause a deterministic FAIL. |
| `INV-16` | `HARD` | Every identity value quoted in the developer report equals the corresponding value in the evidence it claims to describe. |
| `INV-17` | `HARD` | A locale change alters no authority, scope, state or legal effect. |
| `INV-18` | `HARD` | No service-to-service credential, private key or bearer authority is present in the browser. |
| `INV-19` | `HARD` | The governed test fixture is absent from the production build, not merely unreachable in it. |
| `INV-20` | `HARD` | This package never asserts its own acceptance. |
| `INV-21` | `HARD` | A capability whose dependency is a security-sensitive boundary is never reported as supported, and no caller-asserted authorization is treated as evidence that authorization occurred. |

## 7. Capability discipline

A capability may be dependency-blocked if and only if the frontend fails closed for it, names its exact missing dependency, and does not simulate it.

The controlled vocabulary is:

- `SUPPORTED_REAL_PATH`
- `SUPPORTED_WITH_DECLARED_LIMITATION`
- `BLOCKED_BY_DEPENDENCY`
- `UNSUPPORTED`

25 capabilities may be dependency-blocked;
`conflict_restriction_change` must be `UNSUPPORTED` rather than blocked,
because it is a prohibition rather than a missing dependency; and exactly three
capabilities are local real paths that depend on nothing external.

## 8. Evidence

Every authoritative command below writes a raw log, and every evidence record
embeds the binding block measured *at execution time*:

- `schema_version`
- `stage`
- `candidate_state`
- `source_tree_digest`
- `package_lock_sha256`
- `test_source_digest`
- `configuration_digest`
- `command`
- `started_at`
- `finished_at`
- `exit_code`
- `result`
- `raw_report_sha256`

A recorded PASS therefore names the exact source tree that produced it. Stale
evidence is not a judgement call: the digest differs and the run fails.

| Evidence | Raw log |
| --- | --- |
| `format` | `validation/front05/raw/format.log` |
| `typecheck` | `validation/front05/raw/typecheck.log` |
| `lint` | `validation/front05/raw/lint.log` |
| `unit` | `validation/front05/raw/unit-tests.log` |
| `component` | `validation/front05/raw/component-tests.log` |
| `build` | `validation/front05/raw/build.log` |
| `build_production_profile` | `validation/front05/raw/build-production.log` |
| `browser` | `validation/front05/raw/browser.log` |
| `browser_production` | `validation/front05/raw/browser-production.log` |
| `authorization_negative` | `validation/front05/raw/authorization-negative.log` |
| `visual` | `validation/front05/raw/visual.log` |
| `fixture_absence` | `validation/front05/raw/fixture-absence.log` |
| `dependency_audit` | `validation/front05/raw/dependency-audit.log` |

Authoritative result: `validation/front05/authoritative_preseal_result.json`

## 9. The report identity cross-check (G45)

**Rule.** Every 64-hex digest and every numeric size quoted in the developer report must equal the value recorded in the evidence record it names.

**Why it exists.** The FRONT-04 C2 archive was rejected and resealed because the developer report quoted a source_tree_digest from a penultimate run while the sealed tree carried another. The report sat outside the digest-covered boundary, so no gate checked it. This contract closes that hole by making the report's own quoted identities a gated artifact.

## 9a. Security-sensitive dependencies

**Principle.** A dependency that is missing and a dependency that is defective are different findings. A missing dependency becomes a real path when it is built. A defective one must be corrected before it may be relied on at all, and a route appearing over the top of it does not correct it.

**Rule.** A capability whose dependency is classified SECURITY_SENSITIVE_BOUNDARY may only carry status BLOCKED_BY_DEPENDENCY or UNSUPPORTED. It may never be SUPPORTED_REAL_PATH, and it may never be SUPPORTED_WITH_DECLARED_LIMITATION — a declared limitation states the bounds within which something is safe, and there are no bounds within which a self-asserted authorization is safe.

Dependency classes: `ABSENT`, `SECURITY_SENSITIVE_BOUNDARY`, `PROHIBITED`

### SSD-01 — PACK-13 transparency-service

Affects: `publication_proposal_submission`, `publication_state_observation`

**Observed.** Publication has the single state PUBLISHED, and authorization is a caller-supplied actor_is_authorized boolean.

**Finding.** A caller-supplied authorization boolean is a self-asserted authorization: the caller declares its own permission and the service accepts the declaration. The field that looks like an authorization gate is an authorization claim, made by exactly the party the gate exists to constrain. Accepting it as sufficient would let a rendition reach publication carrying nothing but the proposer's own claim of being allowed to publish — which is the separation WS-04 exists to preserve.

**FRONT-05 position.** FRONT-05 does not treat this boolean as evidence that authorization occurred, does not set or send such a flag, and builds no privileged path on it. No port signature contains a field it could be carried in.

**These do not resolve it:**

- adding a proposal route while authorization stays caller-supplied
- having WS-04 set actor_is_authorized itself
- treating a successful call as evidence that authorization occurred
- recording the capability as SUPPORTED_WITH_DECLARED_LIMITATION

**Unblocking condition.** a server-authoritative proposal and authorization contract: a proposal state distinct from PUBLISHED, and an approval decided and recorded by an authority other than the proposer.

**Status until then.** BLOCKED_BY_DEPENDENCY, with publication approval itself remaining prohibited for WS-04 under every dependency state.

**Escalation.** Reported to the accepting authority as a security-relevant finding against PACK-13, not as a FRONT-05 gap.

Enforced by gate `G46` and by `INV-21`.
## 10. Prohibited remedies

If a journey is blocked, these are not available as ways to make it pass:

- inventing a representative or mandate API
- inventing a publication proposal state on the server's behalf
- treating compliance-service RepresentationMandate as an elected mandate
- mocking a blocked production journey
- fabricating citizen cases outside the marked governed test profile
- reporting a compliance obligation as discharged
- regenerating an inherited visual baseline to clear a regression
- softening a mutation instead of closing the gate it exposed
- treating a caller-supplied actor_is_authorized boolean as evidence of authorization
- recording a security-sensitive dependency as a declared limitation rather than a block

## 11. Gates

46 gates. 44 come from the assignment seed; `G45` and `G46` are
added by this contract for the reasons given in sections 9 and 9a.

| ID | Name |
| --- | --- |
| `G01` | `bootstrap_freshness` |
| `G02` | `baseline_identity` |
| `G03` | `accepted_front_lineage` |
| `G04` | `design_preservation` |
| `G05` | `workspace_origin_boundary` |
| `G06` | `route_inventory` |
| `G07` | `api_capability_truth` |
| `G08` | `mandate_scope_inventory` |
| `G09` | `auth_session` |
| `G10` | `step_up` |
| `G11` | `server_authorization_negatives` |
| `G12` | `wrong_mandate_isolation` |
| `G13` | `representative_home` |
| `G14` | `case_queue_detail` |
| `G15` | `case_triage_real_path` |
| `G16` | `confidential_storage_boundary` |
| `G17` | `staff_assignment_boundary` |
| `G18` | `position_workflow` |
| `G19` | `deviation_workflow` |
| `G20` | `version_provenance` |
| `G21` | `meeting_declaration` |
| `G22` | `conflict_recusal` |
| `G23` | `publication_proposal` |
| `G24` | `final_publication_separation` |
| `G25` | `registry_custody_prohibition` |
| `G26` | `eligibility_decision_prohibition` |
| `G27` | `commit_reauthorization` |
| `G28` | `idempotency` |
| `G29` | `concurrency` |
| `G30` | `degraded_mode` |
| `G31` | `browser_storage` |
| `G32` | `service_worker_cache` |
| `G33` | `privacy_telemetry` |
| `G34` | `scoped_search` |
| `G35` | `accessibility` |
| `G36` | `responsive` |
| `G37` | `i18n` |
| `G38` | `real_build` |
| `G39` | `browser_e2e` |
| `G40` | `voting_boundary` |
| `G41` | `dependency_reconciliation` |
| `G42` | `mutation_suite` |
| `G43` | `archive_hygiene` |
| `G44` | `same_bytes_identity` |
| `G45` | `report_identity_crosscheck` |
| `G46` | `security_sensitive_dependency_discipline` |
