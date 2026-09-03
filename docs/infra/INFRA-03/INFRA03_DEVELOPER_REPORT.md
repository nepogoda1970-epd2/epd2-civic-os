# INFRA-03 DEVELOPER REPORT

## Identity

- **Working stage:** `INFRA-03 — Deployment Runtime, Environment Topology & Preview-Readiness Foundation`
- **Mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED` (proposed developer working contract; canonical `main` has not promoted an INFRA-03 stage)
- **Baseline (canonical target read live at gate start and re-read at gate end):** recorded with commit/tree/timestamps and controlling-file digests in `validation/infra03/baseline_identity.json`
- **Source predecessor:** exact accepted INFRA-02 candidate `EPD2_INFRA02_CI_CD_AND_SOFTWARE_SUPPLY_CHAIN_CANDIDATE_0.1.zip`, SHA-256 `d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c`, 15,980,332 bytes, authoritative run `33574647511`, freeze tree digest `c169a2930ab50612076ab3f90468ff03f5ec19e2005c520765a4905e15c51f7d` — verified from the live acceptance record and from staged bytes (`validation/infra03/predecessor_identity.json`)
- **API-06 status:** `NEXT` — no authoritative acceptance exists; gate G41 is truthfully `BLOCKED_FOR_FINAL_SEAL / DEVELOPMENT_MAY_CONTINUE`

## Implemented scope

Everything in assignment §6 that is provable without real hosting: environment catalog, declarative runtime topology, immutable artifact identity, provider-neutral deterministic preview deployment, real PostgreSQL runtime with canonical ledgered migrations and deterministic seed/reset, classified secret injection, three-domain trust delivery with live TLS/mTLS negatives, network segmentation with a default-deny flow inventory, truthful health/readiness/liveness, dependency-aware startup, graceful shutdown, restart accounting, drift detection, idempotent redeploy, schema-safe rollback, failure injection and recovery, voting-domain isolation, privacy-safe observability, resource boundaries, environment isolation and destructive-action safety — all consumed from and bound to the accepted INFRA-02 supply-chain guarantees, never a bypass.

## Runtime topology

`infra/runtime/topology.yaml` (schema `epd2.infra03.topology/1`): six declared network segments (public / application / data / admin_ops / voting / observability) and six services — `ingress-gateway` (the only public endpoint, TLS 1.2+, request limits, forwarded-header replacement), `identity-runtime-shell` and `membership-runtime-shell` (application segment, mTLS, role-scoped PostgreSQL), `voting-runtime-shell` (voting segment: separate voting CA, private observability, identity-header refusal at the boundary), `observability-collector` (mTLS ingest with redaction), and `postgres-preview` (real PostgreSQL 16, TLS + scram-sha-256, peer-auth admin over the instance unix socket only). The admin plane is a local unix socket — no admin TCP port exists. Runtime shells implement infrastructure semantics only; accepted API artifacts are the governed future occupants of the slots (§50).

## Deployment strategy

Process-based, provider-neutral, portable, container-free (the accepted release path declares `NO_CONTAINER_BASE_IMAGES`); one canonical runner (`validation/infra03/run_preview_deployment.py`, driven by the same `scripts/infra03/supervisor.py` the gates use — no second deployment implementation). Deploy sequence: topology lint → artifact digest verification against the acceptance record → extraction and freeze-digest reproduction (`approved == deployed`) → per-deployment PKI → per-instance PostgreSQL (initdb, TLS, roles/databases) → canonical migrations from the _deployed artifact_ under the owning role with a content-hashed ledger → per-service config rendering (classified; fail-closed startup validation, exit 78 on invalid config) → resource-limited service spawn with restart accounting → polled readiness (never sleep) → probes (`observed` digest served by each process on `/identity`). A failed deploy returns non-zero, emits evidence, claims nothing and stops the runtime.

## Network / trust / secrets

Default-deny flow inventory (`validation/infra03/network_flow_inventory.json`, 11 flows F01–F11 with source/destination/protocol/port/purpose/owning requirement); loopback-only binding verified from kernel state; no declared external egress (kernel-level egress filtering is an honest deferred limitation recorded in the evidence). Trust: three per-deployment CAs (application / data / voting), per-workload key pairs (no universal certificate — detected), workload identity carried in CN+SAN and enforced on every connection; wrong CA, wrong hostname, missing client certificate, expired material and foreign-domain identities are all refused live. Secrets: per-deployment generation into an owner-only store, classified slots (`db-credential` only is provisionable; voting-domain key material is _never_ provisionable by INFRA-03), value-exact leak scanning over repository/manifests/configs/logs/evidence, and manifest scanning — zero values anywhere outside the store.

## PostgreSQL / migrations

Real PostgreSQL 16 (16.13 in the gate environment; version string recorded from the live cluster). Proven: TLS-only TCP (`hostnossl … reject`; plaintext refused live), scram-sha-256, role/database credential isolation (cross-database connect refused), transactions (rollback leaves no state), reconnect, outage fail-closed readiness, restart persistence, ledgered canonical migrations from the deployed artifact (10 applied for `epd2_identity`; re-apply is a no-op; changed history is refused), deterministic synthetic fixtures, and clean reset with machine proof that pre-reset state is gone.

## Preview deployment / reset

Deterministic clean-room deployment (dirty instance directories refused, negative control in evidence) reaching full readiness in seconds; destroy/reset require the exact environment + instance identity and refuse ambiguous or production-like targets. Seed/reset hooks: fixture SQL through the canonical schema, drop/recreate/re-migrate/re-seed with stale-state proof and deterministic reseed.

## Failure / recovery / rollback

Injected and classified live: DB outage (`FAIL_CLOSED` readiness / liveness stays true), observability outage (`EXPLICIT_UNAVAILABLE` collector, `SAFE_RETRY` producers, application readiness unaffected), DNS failure (`EXPLICIT_UNAVAILABLE`), consequential operations exactly-once across outage and retry (`SAFE_RETRY` with duplicate refusal), recovery to ready without restart after dependency restoration. Redeploy of the identical release is idempotent; a foreign artifact is refused. Rollback only ever selects the previously verified release; rollback past applied migrations and rollback to unknown digests are refused (schema safety).

## Voting isolation

Enforced live and scanned: identity/correlation headers (`X-Member-Id`, `X-Person-Id`, `X-Account-Id`, `X-Session-Id`, `X-Correlation-Id`, …) are refused with 403 at the voting boundary; application-CA client identities cannot complete a handshake in the voting segment; voting telemetry goes to a private sink only — the shared collector is proven voting-free; telemetry scans refuse person/member/account/session shapes and the application correlation-id namespace. No voting key material exists in preview and none is provisionable by this stage.

## Provider / sovereignty assumptions

No commercial cloud or hosting provider is selected or referenced; the deployment is process-based and portable; locks are byte-identical to the accepted predecessor (no provider SDK entered the release identity); all trust material is standard X.509 generated per instance — no provider-only opaque mechanism is required to establish any cryptographic truth (FIR-INFRA-SOV-001 preserved).

## BSI readiness impact

`validation/infra03/bsi_readiness_disposition.json`: touched rows M-16/M-17/M-19/M-25 (segmentation, TLS/mTLS proofs, secret handling, logging privacy) advanced as preparatory readiness; the nine previously deferred gaps are unchanged; `new_certification_blockers = []`; the hard freeze — **no persistent member/person identifier inside the voting domain** — is preserved and enforced live. No certification claim.

## Gates

See `validation/infra03/infra03_preseal_result.json` (42 gates). Final run: **39 PASS, 0 FAIL, G41 `BLOCKED_FOR_FINAL_SEAL / DEVELOPMENT_MAY_CONTINUE`** (API-06 unaccepted — never faked as PASS); G39/G40 (archive hygiene, same-bytes identity) are executed by the packaging phase via the canonical acceptance harness (51/51 checks, registry 2.0.0), whose archive-side hygiene, frozen-artifact, secret and byte-identity gates apply to the working archive, with the detached preseal record carrying the final SHA-256/size.

## Mutation suite

- Total classes: **36** (`scripts/infra03/mutations.py`)
- Detected: **36/36**, each by its own distinct `I03_*` detector (distinctness proven by a closing test); trust classes proven with real TLS handshakes, artifact classes with real ZIP bytes, lifecycle classes against the same evaluators the gates execute; plus a live fail-closed mini-deploy for partial-exposure
- Missed: **0**

## Outstanding reconciliation

Final seal/acceptance of INFRA-03 is **blocked** until: (1) canonical governance explicitly permits/promotes INFRA-03 or equivalent scope; (2) API-06 is authoritatively accepted and its exact accepted bytes are reconciled with affected gates rerun; (3) current PCR/Master are refreshed at that seal. Items marked for later CTRL reconciliation: final privileged-authority semantics of the admin plane (§48, §52). OPS-02's accepted preview-operations foundation is acknowledged as concurrent accepted work and is not duplicated here.

## Candidate identity

- **File:** `EPD2_INFRA03_DEPLOYMENT_RUNTIME_AND_PREVIEW_READINESS_WORKING_0.1_PRESEAL.zip`
- **SHA-256 / Size:** the archive digest cannot appear inside the archive; the exact values are emitted by the packaging phase as `INFRA03_PRESEAL_RESULT:PASS:<sha256>:<size>` with a detached `.sha256` sidecar and a detached final preseal record delivered alongside this candidate. The in-archive identity anchors are the git commit, tree and freeze tree digest in the sealed execution manifest and `validation/infra03/` evidence.

## Self-state

```text
IMPLEMENTATION_COMPLETE
LOCAL_VERIFICATION_PASS
PRESEAL_READY
NOT_ACCEPTED
```

`NOT_ACCEPTED`. No developer-created acceptance record exists; nothing here is an `AUTHORITATIVE_RESULT`. No INFRA acceptance/closure, production readiness, system-trial pass, OPS closure, SEC pass, legal activation or BSI/CC/EAL4 certification follows from this candidate.
