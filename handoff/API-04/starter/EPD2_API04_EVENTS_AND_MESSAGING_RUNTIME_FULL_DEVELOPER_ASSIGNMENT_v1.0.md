# EPD² API-04 — Events & Messaging Runtime / Delivery Semantics

**Assignment version:** 1.0  
**Date:** 2026-08-31  
**Execution mode:** `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`  
**Current deliverable:** `EPD2_API04_EVENTS_AND_MESSAGING_RUNTIME_WORKING_0.1_PRESEAL.zip`

This is the implementation assignment. It is not acceptance evidence and does not authorize API-04 closure.

---

# 1. Entry status and lineage discipline

API-04 development starts immediately. Do not wait for API-02/API-03 governance closure.

Current dependency treatment:

```text
API-02 = authoritative acceptance/correction still in progress
API-03 R13 = externally verified working implementation / PRESEAL / NOT FINAL ACCEPTED PREDECESSOR
API-04 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED
```

API-03 R13 may be used only as:

`WORKING_INTEGRATION_PREDECESSOR`

It must not be recorded as:

`ACCEPTED_PREDECESSOR`

Final API-04 predecessor SHA, lineage freeze, sealed C1 inventory, final acceptance workflow inputs and final candidate packaging are forbidden until API-03 receives independent `ACCEPTED / CLOSED` status after exact accepted API-02 reconciliation.

The developer develops and verifies API-04 locally/preseal and returns the required package. The developer must not self-declare authoritative acceptance. Independent governed acceptance is performed separately after predecessor reconciliation.

---

# 2. Mandatory bootstrap order

Before changing code, read in this order:

1. `docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md`
2. current `docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md`
3. current `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`
4. the API-stage contracts/handover required by the PCR
5. current BSI voting bootstrap/readiness documents whenever a change can affect the voting trust boundary
6. accepted DATA terminal baseline records
7. accepted API-01 gateway/BFF boundary records
8. current API-02 contracts relevant to principal/session/authorization semantics
9. API-03 R13 in full, especially service identity, S2S authentication, S2S authorization, credential lifecycle, trust boundaries, validator and handover
10. PACK-13 Production Data Plane / Contract Evolution documents and current event/outbox/inbox/schema-registry implementation.

If Entrypoint, PCR, Master, stage contracts, candidate contents or evidence materially disagree: stop, record the conflict and reconcile it. Never silently choose the older statement.

---

# 3. Stage objective

Productionize the internal asynchronous integration boundary:

```text
authoritative domain transaction
→ transactional outbox
→ authenticated producer
→ governed broker/topic
→ at-least-once transport
→ authenticated consumer
→ inbox/dedup/idempotent effect
→ durable acknowledgement
```

The required contract is:

```text
AT-LEAST-ONCE DELIVERY
+
EFFECTIVELY-ONCE CONSUMER EFFECT
```

Do not claim generic `EXACTLY ONCE` transport semantics.

Hard semantic separation:

```text
message transport != domain authority
broker state != domain truth
broker ACL != business authorization
delivery once != effect once
```

---

# 4. Hard architectural invariants

## 4.1 Messaging infrastructure is not a domain owner

The broker, dispatcher, router, schema registry and consumer framework may transport and validate messages. They may not decide membership, voting eligibility, finance authority, governance outcomes, office/mandate state, conflict status, casework decisions or any other owning-domain truth.

## 4.2 Service identity comes from API-03

Producer and consumer identity must derive from verified API-03 service identity. Never trust request/message supplied `producer_service`, `consumer_service`, `service_id`, roles, scope or authority merely because they appear in headers or payload.

A human/member bearer token is not a service identity.

## 4.3 No global person identity through messaging

Do not propagate a universal `user_id`, `person_id`, `account_id`, `member_id`, email, phone or equivalent stable human identifier as a generic cross-service correlation key. Use purpose/domain-scoped references only.

## 4.4 Voting boundary remains isolated

The ordinary messaging bus must not become a member/account/person → voting credential → ballot/tally correlation channel. General broker paths must not carry prohibited stable network, tracing or correlation metadata into WS-03.

Where API-04 touches a voting-affecting path, apply the BSI readiness bootstrap and identify the touched readiness rows. No certification/compliance claim is permitted.

## 4.5 Fail closed

Unknown producer, consumer, topic, schema, schema version, service identity, ACL, organization scope, retry disposition, replay authority or event type must not silently become accepted.

---

# 5. Transactional outbox

Productionize the PACK-13 outbox contract.

Required invariant:

```text
domain state + outbox event = same DB transaction
```

Prove at minimum:

- no publish before transaction commit;
- rollback creates no publishable event;
- successful domain commit cannot lose its required outbox event;
- stable event ID exists before commit;
- dispatcher leasing is durable;
- stale lease recovery works;
- dispatcher crash/restart is safe;
- publish acknowledgement is durably recorded;
- retries are bounded and reason-coded;
- published event payload/version is immutable;
- pending/old outbox entries are observable.

Do not claim XA/distributed transactions unless actually implemented and proven.

---

# 6. Real broker runtime

API-04 must contain a real broker-backed runtime path. In-memory/mock transports may remain for unit tests but cannot be the sole runtime/evidence.

If a permanent broker product has not been governed yet, use:

```text
transport-neutral port
+ reproducible real reference broker adapter
```

and do not claim the adapter is the final INFRA product choice.

Pin the exact broker/server version. Never use `latest`.

Required capabilities:

- publish;
- durable subscription;
- consumer position;
- reconnect/redelivery;
- producer and consumer restart;
- backpressure;
- bounded retries;
- dead-letter/quarantine;
- authenticated connection;
- topic ACL;
- no anonymous protected publisher/consumer.

---

# 7. Topic / stream / subscription registry

Build a machine-readable registry derived from runtime truth.

For every active topic/stream/subscription record at least:

- topic ID;
- domain owner;
- allowed producer services;
- allowed consumer services;
- event types;
- schema versions;
- organization/domain scope;
- data classification;
- retention;
- ordering model;
- partition key semantics;
- dedup requirement;
- retry policy;
- DLQ/quarantine policy;
- replay/redrive permission;
- readiness dependency;
- voting-isolation class;
- consequential-effect flag;
- commit-reauthorization requirement.

No active runtime topic may be absent from the registry. No documentation-only topic may be represented as active runtime truth.

---

# 8. Event envelope

Preserve the existing canonical PACK-13 event envelope. Do not create a competing API-04 envelope.

It may carry only governed metadata, such as event ID/type/schema version, verified producer reference, scoped organization/domain reference, occurred-at, causation/provenance, permitted correlation reference, idempotency key, classification and disposition profile.

Correlation IDs must remain operation/request scoped and must not become hidden global person identifiers.

Historical envelope/schema semantics must remain retrievable.

---

# 9. Delivery semantics and durable inbox/dedup

Duplicates are normal transport behavior. Duplicate domain effects are not.

Consequential consumers must use durable duplicate protection with storage-level uniqueness and atomicity between the domain effect and processed/dedup marker where the owning service requires it.

Required cases:

- duplicate event → one effect;
- lost acknowledgement → safe redelivery;
- consumer crash before ack → safe redelivery;
- consumer crash after durable effect but before ack → no second effect;
- producer lost-response retry → no duplicate domain effect;
- same idempotency key with different payload → hard refusal;
- dedup retention covers the governed replay/redelivery horizon.

An in-memory `set()` is not production dedup evidence.

---

# 10. Ordering

No global-order fiction.

Every governed event class must explicitly declare one ordering model, e.g.:

```text
UNORDERED
PER_AGGREGATE
PER_ORGANIZATION
PER_PARTITION
SEQUENCE_VERSIONED
```

Where domain semantics require ordering, stale/out-of-order events must be explicitly rejected, quarantined or reconciled. Producer wall-clock time is not authoritative event order.

---

# 11. Retry, DLQ and quarantine

At minimum classify:

- transient failure;
- dependency unavailable;
- rate/backpressure;
- invalid service identity;
- unauthorized producer/consumer;
- malformed event;
- incompatible/unknown schema;
- poison event;
- stale event;
- expired/deadline-invalid queued work;
- permanently forbidden effect;
- unknown event type.

Required shape:

```text
bounded retries → exhausted → reason-coded quarantine/DLQ
```

No poison-message infinite loop. No silent drop.

DLQ evidence must be sufficient for investigation without copying secrets or unnecessary sensitive payloads.

---

# 12. Governed re-drive and replay

Manual DLQ redrive is a governed action. Record immutable evidence of source item, authenticated operator/service principal, authority, reason, target, time, replay range, schema result and current state/authorization result where consequential.

No arbitrary `requeue all` path.

Replay is separate from ordinary retry. Support, when governed:

- exact-message replay;
- bounded range replay;
- selected-consumer replay;
- projection rebuild.

Before consequential replay evaluate current schema compatibility, retention/legal hold, authorization, object state, policy and idempotency semantics.

A historical event must not silently acquire new meaning because current code is newer.

---

# 13. Schema registry and contract evolution

Productionize the existing PACK-13 canonical registry. Do not create a second API-04 schema registry.

Required:

- stable event/schema IDs;
- explicit versions;
- deterministic compatibility checker;
- producer allowed-version policy;
- consumer accepted-version policy;
- breaking-change gate;
- unknown version fails closed;
- historical schema retrievable;
- no `latest`-only interpretation.

---

# 14. Producer / consumer ACL

Broker ACL is necessary transport control, not domain authorization.

Publish authorization must bind verified API-03 service principal + allowed producer + topic + event type + schema version + scope + data classification.

Consume authorization must bind verified API-03 service principal + subscription owner + allowed consumer + topic + scope + data classification + compatible contract.

No universal service account or wildcard `*:*` authority for protected messaging.

---

# 15. FIR-AUTH-001 and queued consequential work

A message may remain queued while authority, scope, object state or policy changes. Inventory every asynchronous path capable of producing a consequential effect.

Mandatory negative cases:

- role/authority revoked while queued;
- service authority/credential revoked;
- organization scope changed;
- object state/version changed;
- deadline expired;
- policy/legal-effect version changed;
- delayed redelivery after long outage;
- replay after authority loss.

Where required by the owning domain:

```text
consume → prepare → revalidate current authority/scope/assurance/state → final authoritative commit
```

Transport arrival is never sufficient authorization for a consequential commit.

---

# 16. Readiness, lag and stale-state protection

Preserve the project rule:

```text
process alive != service ready
service ready != authoritatively ready
```

API-04 readiness should cover at least:

- broker connectivity;
- required topic/subscription availability;
- API-03 service identity readiness;
- schema registry readiness;
- PostgreSQL migration readiness;
- outbox dispatcher health;
- consumer lag;
- projection watermark/freshness;
- blocking DLQ/quarantine condition;
- recovery/reconciliation state.

A consequential operation must not silently rely on a stale projection.

---

# 17. Backpressure and overload

Implement bounded concurrency/memory, visible queue/lag state, pause/resume, producer throttling and safe overload behavior. Do not drop consequential messages merely to reduce lag.

---

# 18. PostgreSQL persistence

Use the governed PostgreSQL line for production-reference outbox, inbox/dedup, dispatcher state and replay/redrive evidence where appropriate.

Storage-level uniqueness and concurrency controls must protect delivery/effect semantics.

Use the exact current governed PostgreSQL version for authoritative/preseal reproduction (currently 16.15 unless current canonical authority changes it before freeze).

Do not reopen or reclassify accepted DATA work. Prove no-new-regression against the accepted DATA baseline.

---

# 19. Privacy, evidence, retention and legal hold

Operational evidence may record throughput, lag, latency, retries, DLQ count, outbox age, schema/auth refusals, replay/redrive and readiness.

Never persist in ordinary logs/evidence:

- Authorization credentials;
- service/session/access/refresh tokens;
- cookies;
- passwords;
- private keys;
- secret-bearing environment values;
- unnecessary complete sensitive event payloads;
- prohibited person/member/voting correlation identifiers.

Treat broker payloads, outbox, inbox, DLQ and projections as derived copies for retention/disposition/legal-hold analysis. Prefer minimized event payloads over cloning whole domain records into the bus.

---

# 20. Mandatory documentation package

Create one canonical directory:

`docs/api/API-04/`

Minimum:

1. `01_EXECUTIVE_RESULT.md`
2. `02_SCOPE_AND_BOUNDARIES.md`
3. `03_ENTERING_BASELINE_AND_PARALLEL_STATUS.md`
4. `04_EVENT_AND_MESSAGE_ENVELOPE.md`
5. `05_TRANSACTIONAL_OUTBOX.md`
6. `06_BROKER_RUNTIME.md`
7. `07_DELIVERY_AND_IDEMPOTENCY.md`
8. `08_ORDERING_AND_VERSIONING.md`
9. `09_RETRY_DLQ_QUARANTINE.md`
10. `10_REPLAY_AND_REDRIVE.md`
11. `11_SCHEMA_AND_COMPATIBILITY.md`
12. `12_SERVICE_IDENTITY_AND_ACL_BOUNDARY.md`
13. `13_CONSEQUENTIAL_ASYNC_REAUTHORIZATION.md`
14. `14_READINESS_LAG_AND_STALE_STATE.md`
15. `15_PRIVACY_RETENTION_AND_VOTING_ISOLATION.md`
16. `16_THREAT_MODEL.md`
17. `17_TEST_EVIDENCE.md`
18. `18_OPEN_GAPS.md`
19. `19_HANDOVER_TO_API05.md`
20. `API04_LINEAGE.json`
21. `API04_TOPIC_AND_SUBSCRIPTION_REGISTER.json`
22. `API04_EVENT_SCHEMA_REGISTER.json`
23. `API04_PRODUCER_CONSUMER_ACL_MATRIX.json`
24. `API04_DELIVERY_SEMANTICS_MATRIX.json`
25. `API04_CONSEQUENTIAL_ASYNC_REGISTER.json`
26. `API04_REPLAY_REDRIVE_POLICY.json`
27. `API04_FAILURE_INJECTION_MATRIX.json`
28. `API04_PRESEAL_INVENTORY.json`
29. `API04_PRESEAL_FILE_MANIFEST.json`
30. `PROGRAM_CONTROL_REGISTER_UPDATE_PROPOSAL.md`

Do not create competing dossiers with ambiguous authority.

---

# 21. Validator

Create:

`scripts/validate_api04.py`

Mandatory gates:

```text
G0   archive/root/hygiene
G1   canonical governance
G2   PRESEAL status correctness
G3   API-03 R13 recorded only as working predecessor
G4   inventory/accounting
G5   canonical event-envelope uniqueness
G6   runtime topic/subscription registry
G7   service identity + ACL
G8   transactional outbox
G9   durable inbox/dedup
G10  ack/crash/redelivery
G11  ordering/versioning
G12  schema compatibility
G13  retry/DLQ/quarantine
G14  replay/redrive governance
G15  async FIR-AUTH-001
G16  readiness/lag
G17  identifier/privacy governance
G18  voting isolation / BSI readiness impact
G19  retention/legal hold
G20  real broker runtime
G21  live PostgreSQL runtime
G22  inherited API-chain non-regression
G23  DATA no-new-regression
G24  cross-service failure fixtures
G25  secret/evidence sanitation
G26  mutation self-test
G27  no API-05+ scope leakage
```

Preseal terminal success line:

`API04_PRESEAL_RESULT:PASS:validation/api04/validator_result.json`

After exact accepted API-03 reconciliation, the final candidate validator may use:

`API04_RESULT:PASS:validation/api04/validator_result.json`

Any mandatory gate not executed is not PASS.

---

# 22. Mandatory adversarial mutation suite

The validator must automatically detect at minimum:

1. publish before domain commit;
2. committed state with missing required outbox event;
3. duplicate message causes duplicate effect;
4. lost ack causes second effect;
5. same idempotency key + different payload accepted;
6. dispatcher crash after publish creates unsafe state;
7. consumer crash after effect/before ack creates second effect;
8. stale lease cannot recover;
9. infinite poison retry;
10. poison event silently dropped;
11. unauthorized producer accepted;
12. unauthorized consumer accepted;
13. message-supplied service identity trusted;
14. human token accepted as service identity;
15. revoked API-03 credential accepted;
16. protected unknown topic auto-created;
17. unknown event type accepted;
18. unknown/incompatible schema accepted;
19. unauthorized producer schema version accepted;
20. consumer silently parses incompatible schema;
21. stale aggregate version overwrites newer state;
22. global ordering assumed without contract;
23. historical event reinterpreted under new semantics;
24. replay after authority revocation creates effect;
25. unauthorized DLQ redrive;
26. redrive to wrong target;
27. stale projection reported ready;
28. consequential action ignores lag/freshness;
29. broker outage treated as successful publish;
30. schema-registry outage fails open;
31. wildcard universal protected service ACL;
32. global `person_id`/equivalent added to generic envelope;
33. email/member number used as generic correlation ID;
34. voting event contains member/account identity;
35. voting path receives prohibited network/correlation identity;
36. DLQ leaks a credential/token;
37. sensitive payload dumped to persistent logs/evidence;
38. dedup retention shorter than replay horizon;
39. disposition/legal-hold rule ignored;
40. API-04 PRESEAL self-claims `ACCEPTED`/`CLOSED`;
41. API-03 R13 falsely labelled `ACCEPTED_PREDECESSOR`;
42. API-05 external-integration/provider semantics pulled into API-04.

---

# 23. Mandatory cross-service failure fixtures

Run real/integration fixtures for at least:

- duplicate event;
- delayed event;
- out-of-order event;
- lost publish response;
- lost consume acknowledgement;
- producer crash;
- consumer crash;
- broker restart;
- producer/consumer restart;
- broker disconnect/reconnect;
- schema registry unavailable;
- stale producer schema;
- stale consumer schema;
- API-03 identity unavailable;
- service credential revoked;
- DLQ + governed redrive;
- consumer lag;
- stale projection;
- authority revoked while queued;
- deadline expires while queued;
- object version changes while queued;
- restore/replay after prior revocation.

These fixtures are cumulative evidence for the repository-wide incremental cross-service failure requirement; they do not by themselves close the entire repository-wide FIR.

---

# 24. API-03 reconciliation boundary

Keep the API-03 dependency behind an explicit adapter/interface.

When the exact accepted API-03 predecessor becomes available:

1. mechanically compare working R13 against exact accepted API-03;
2. enumerate all differences relevant to API-04;
3. reconcile adapters/contracts only where required;
4. rerun all API-04 tests and validator gates;
5. bind exact accepted API-03 archive name/SHA and acceptance evidence;
6. regenerate final predecessor-to-C1 inventory;
7. regenerate final sealed manifest/checksums;
8. replace PRESEAL status with `CANDIDATE_NOT_ACCEPTED`;
9. only then assemble final C1.

Do not restart API-04 merely because the predecessor status changed. Restart only for a real governed incompatibility/regression.

---

# 25. Current developer deliverable

Return exactly:

1. `EPD2_API04_EVENTS_AND_MESSAGING_RUNTIME_WORKING_0.1_PRESEAL.zip`
2. SHA-256 sidecar;
3. split-part manifest if transport splitting is necessary;
4. concise developer report recording:
   - working predecessor identity;
   - implementation areas;
   - real broker/version;
   - PostgreSQL result;
   - runtime topic/subscription count;
   - producer/consumer binding count;
   - outbox result;
   - inbox/idempotency result;
   - schema compatibility result;
   - replay/DLQ/redrive result;
   - readiness/lag result;
   - failure-fixture result/count;
   - mutation result/count;
   - inherited API/Data regression results;
   - voting/BSI readiness impact rows, if touched;
   - open gaps;
   - exact API-03 reconciliation checklist.

Archive status must be exactly:

`PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`

Forbidden current claims:

```text
API-04 ACCEPTED
API-04 CLOSED
FINAL PASS
API-05 NEXT
API-03 ACCEPTED PREDECESSOR
PRODUCTION READY
```

---

# 26. Future final C1

After API-03 is independently accepted and reconciliation completes, assemble:

`EPD2_API04_EVENTS_AND_MESSAGING_RUNTIME_CANDIDATE_0.1_C1.zip`

Its internal status must remain:

`CANDIDATE_NOT_ACCEPTED`

until a separate independent authoritative acceptance run passes on the exact sealed bytes.

Only then may governance record:

```text
API-04 = ACCEPTED / CLOSED
API-05 = NEXT
```

---

# 27. Definition of done for current parallel development

```text
canonical governance read
+ API-03 R13 integration behind adapter boundary
+ real broker runtime
+ PostgreSQL outbox/inbox/dedup
+ at-least-once delivery
+ effectively-once consumer effects
+ schema evolution/runtime registry
+ service-identity ACL
+ ordering
+ retry/DLQ/quarantine/redrive
+ governed replay
+ queued-work reauthorization
+ readiness/lag protection
+ privacy/retention/voting isolation
+ failure fixtures
+ mutation suite
+ preseal validator PASS
= API-04 WORKING PRESEAL READY FOR PREDECESSOR RECONCILIATION
```
