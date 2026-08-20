# PB01-I10 C6 Final Acceptance Result

- Verdict: **FAIL**
- Workflow run: 32385596761
- Commit: 16192e3dda4d7f1a527c755fa80f99af6df27056
- Candidate: EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C6.zip
- Expected / reconstructed SHA-256: 442b83d9639a7398b3da767beb95976d379190229610d9b5ccb550d53d277d25
- validate:i10 outcome: failure

```json
```

## Validation progress tail
```text
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 350.043398
✔ I09 C1/PG 4 execute callers use 4 independent stores/DB transactions and converge (240.801183ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 333.558353
✔ I09 C1/PG 2 execute callers use 2 independent stores/DB transactions and converge (232.779067ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 322.677941
✔ I09/PG deterministic injected 40001 remains a retry-policy test only (1456.888796ms)
✔ I09/PG retry budget exhausted produces explicit operational failure and no tally (225.320983ms)
✔ I09/PG non-retryable database SQLSTATE fails immediately (153.974317ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1926.143109
✔ I09 C1/PG burst produces 40001 from real concurrent SERIALIZABLE transactions and converges (247.23096ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 342.746384
✔ I09 C1 mixed A: tally during uncommitted finalization fails closed, retry after commit yields one canonical tally (233.577691ms)
✔ I09 C1 mixed B: publication cannot cross an uncommitted decryption boundary (852.552378ms)
✔ I09 C1 mixed C: read-only verifier sees no bundle during publication transaction, then complete canonical bundle PASS (695.173538ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1884.204404
{"status":"C1_CONCURRENCY_AND_MIXED_PASS","postgresql_version":"postgres (PostgreSQL) 16.15 (Ubuntu 16.15-1.pgdg24.04+2)"}
[I10_PROGRESS] PASS label="i09:concurrency" elapsed_ms=14287
[I10_PROGRESS] START label="i09:crash" timeout_ms=600000

> epd2-pb01-i06-candidate@0.1.0 test:i09:crash
> bash scripts/run_i09_postgres_class.sh tests/i05-postgres-crash-restart.test.mjs tests/i06-postgres-concurrency-crash.test.mjs tests/i07-postgres-crash.test.mjs

✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (633.409848ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (734.090029ms)
✔ I06/PG concurrent final threshold shares converge to one immutable record (831.505596ms)
✔ I06/PG same-guardian concurrent duplicate race never double-counts threshold (271.307077ms)
✔ I06/PG CRASH-01 retry deterministically converges (626.613231ms)
✔ I06/PG CRASH-02 retry deterministically converges (499.522332ms)
✔ I06/PG CRASH-03 retry deterministically converges (627.229522ms)
✔ I06/PG CRASH-04 retry deterministically converges (532.052616ms)
✔ I07/PG crash before_result_persistence leaves no incomplete FINAL and retry converges (1213.537789ms)
✔ I07/PG crash after_result_persistence_before_evidence_publication_marker leaves no incomplete FINAL and retry converges (886.998456ms)
✔ I07/PG crash after_evidence_persistence_before_final_status_transition leaves no incomplete FINAL and retry converges (873.718631ms)
✔ I07/PG crash immediately after FINAL commit before response preserves one final result and retry is idempotent (875.340312ms)
ℹ tests 12
ℹ suites 0
ℹ pass 12
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 8883.253197
[I10_PROGRESS] PASS label="i09:crash" elapsed_ms=10216
[I10_PROGRESS] START label="i09:restart" timeout_ms=600000

> epd2-pb01-i06-candidate@0.1.0 test:i09:restart
> bash scripts/run_i09_postgres_class.sh tests/i05-postgres-crash-restart.test.mjs tests/i06-postgres-restart-backup.test.mjs tests/i07-postgres-restart-backup.test.mjs

✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (640.897665ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (638.157286ms)
✔ I06/PG hard database crash/restart preserves same immutable plaintext and record digest (1122.455439ms)
✔ I06/PG backup/restore preserves exact public ceremony/share/decryption evidence and no private guardian columns exist (773.916142ms)
✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (1686.048455ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1278.965376ms)
ℹ tests 6
ℹ suites 0
ℹ pass 6
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 6409.588774
[I10_PROGRESS] PASS label="i09:restart" elapsed_ms=8036
[I10_PROGRESS] START label="i09:backup-restore" timeout_ms=600000

> epd2-pb01-i06-candidate@0.1.0 test:i09:backup-restore
> bash scripts/run_i09_postgres_class.sh tests/i07-postgres-restart-backup.test.mjs

✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (1793.804686ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1338.924211ms)
ℹ tests 2
ℹ suites 0
ℹ pass 2
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3226.645725
[I10_PROGRESS] PASS label="i09:backup-restore" elapsed_ms=4601
[I10_PROGRESS] START label="i09:postgres-full" timeout_ms=1200000

> epd2-pb01-i06-candidate@0.1.0 test:i09:postgres
> I09_PG_STAGE=i03 bash scripts/run_i09_postgres_class.sh tests/postgres.integration.test.mjs tests/postgres-crash-concurrency.test.mjs tests/postgres-tamper-backup-roles.test.mjs && I09_PG_STAGE=i04 bash scripts/run_i09_postgres_class.sh tests/i04-finalization.integration.test.mjs tests/i04-concurrency-crash.test.mjs tests/i04-tamper-backup-roles.test.mjs && I09_PG_STAGE=i05 bash scripts/run_i09_postgres_class.sh tests/i05-postgres.integration.test.mjs tests/i05-postgres-runtime.test.mjs tests/i05-postgres-crash-restart.test.mjs tests/i05-postgres-tamper-backup-roles.test.mjs && I09_PG_STAGE=i06 bash scripts/run_i09_postgres_class.sh tests/i06-postgres-ceremony-decryption.test.mjs tests/i06-postgres-concurrency-crash.test.mjs tests/i06-postgres-restart-backup.test.mjs tests/i06-postgres-tamper-roles.test.mjs && I09_PG_STAGE=i07 bash scripts/run_i09_postgres_class.sh tests/i07-postgres-publication.test.mjs tests/i07-postgres-crash.test.mjs tests/i07-postgres-tamper.test.mjs tests/i07-postgres-restart-backup.test.mjs

✔ PG concurrent same key and same digest create one logical acceptance (139.819418ms)
✔ PG concurrent legitimate revotes coexist under one private lifecycle (77.670774ms)
✔ PG CRASH-01 after crypto before transaction leaves no accepted state (54.044004ms)
✔ PG CRASH-02/04 committed response loss survives service restart and retry (81.514969ms)
✔ PG CRASH-03 client disconnect cannot lose a committed acceptance (77.902424ms)
✔ PG append-only triggers and hash-chain checkpoint detect privileged tampering (161.020004ms)
✔ PG backup/restore preserves exact bytes, receipt state, ledger and private/public split (189.322234ms)
✔ PG submission runtime and evidence reader have no DDL or mutation authority (53.489768ms)
✔ PG-I03-P01 real I02 ballot follows native verification and PostgreSQL acceptance (163.404805ms)
✔ PG-I03-P02 idempotent retry returns same receipt; same key with different ballot conflicts (111.056191ms)
ℹ tests 10
ℹ suites 0
ℹ pass 10
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1344.270655
✔ I04 concurrent identical and conflicting finalizers converge without split state (158.954995ms)
✔ I04-CRASH-01 is atomic and retry converges (113.129446ms)
✔ I04-CRASH-02 is atomic and retry converges (105.375265ms)
✔ I04-CRASH-03 is atomic and retry converges (105.04151ms)
✔ I04-CRASH-04 is atomic and retry converges (101.025586ms)
✔ I04 submission-versus-closure race has one deterministic boundary outcome (113.242257ms)
✔ I04 real I03 revote E2E selects latest valid, preserves history and exact bytes (191.905028ms)
✔ I04 multi-lifecycle resolution yields A2, B1 and C3 in I01 digest order (204.657268ms)
✔ I04 empty election finalizes deterministically (74.909914ms)
✔ I04 public verifier detects every committed-field tamper class (190.51559ms)
✔ I04 refuses finalization when I03 ledger integrity has been altered (99.280851ms)
✔ I04 PostgreSQL roles enforce submission/finalizer/evidence/migration separation (192.957607ms)
✔ I04 backup/restore preserves exact I03 history and identical final artifacts (409.148853ms)
ℹ tests 13
ℹ suites 0
ℹ pass 13
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2315.183754
✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (647.579197ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (634.766615ms)
✔ I05/PG exact finalized I04 set becomes the tally input and native Belenios re-verification runs per ballot (230.122927ms)
✔ I05/PG idempotent retry replays one physical tally without recomputing a second record (216.792644ms)
✔ I05/PG concurrent tally executions never diverge and every caller converges on one identical tally (161.572417ms)
✔ I05/PG rejects a conflicting F_final and a conflicting tally record against the same election (190.95899ms)
✔ I05/PG recompute reproduces the committed tally byte-for-byte from PostgreSQL state (266.463801ms)
✔ I05/PG append-only triggers reject mutation of committed tally state even for the schema owner (231.8662ms)
✔ I05/PG privileged tamper that bypasses the triggers is still detected by evidence and recompute (221.863362ms)
✔ I05/PG tally runtime cannot mutate I03 or I04 state (169.138594ms)
✔ I05/PG submission, finalizer and evidence roles cannot mutate I05 tally state (187.742002ms)
✔ I05/PG tally and evidence roles hold no DDL or TEMP privilege anywhere (158.253284ms)
✔ I05/PG backup and restore preserve exact aggregate and tally bytes and every digest (428.815002ms)
✔ I05 PostgreSQL exact finalized set tally, idempotency, recompute, concurrency and privileges (285.291057ms)
✔ I05 PostgreSQL CRASH-03 rolls aggregate insert back; retry converges (185.329212ms)
ℹ tests 15
ℹ suites 0
ℹ pass 15
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 4572.210768
✔ I06/PG real threshold ceremony freezes immutable N=3 T=2 public context (483.28758ms)
✔ I06/PG T-1 exposes no plaintext; exact threshold commits one immutable result; extra valid share cannot change plaintext (695.914817ms)
✔ I06/PG duplicate guardian and malformed/invalid share fail closed (411.091736ms)
✔ I06/PG concurrent final threshold shares converge to one immutable record (830.865716ms)
✔ I06/PG same-guardian concurrent duplicate race never double-counts threshold (276.449475ms)
✔ I06/PG CRASH-01 retry deterministically converges (691.025913ms)
✔ I06/PG CRASH-02 retry deterministically converges (508.394437ms)
✔ I06/PG CRASH-03 retry deterministically converges (616.973026ms)
✔ I06/PG CRASH-04 retry deterministically converges (530.037053ms)
✔ I06/PG hard database crash/restart preserves same immutable plaintext and record digest (1324.665955ms)
✔ I06/PG backup/restore preserves exact public ceremony/share/decryption evidence and no private guardian columns exist (765.199512ms)
✔ I06/PG mandatory I05 corrective detects privileged aggregate-byte-only rewrite and decryption refuses (811.251908ms)
✔ I06/PG privileged tamper: guardian public key after freeze is detected (407.739451ms)
✔ I06/PG privileged tamper: threshold after ceremony freeze is detected (405.865501ms)
✔ I06/PG privileged tamper: frozen guardian-set member replacement is detected (396.843957ms)
✔ I06/PG privileged tamper: partial-decryption factor bytes are detected (421.394843ms)
✔ I06/PG privileged tamper: partial-decryption proof bytes are detected (416.55837ms)
✔ I06/PG privileged tamper: accepted share digest column is detected (411.42739ms)
✔ I06/PG privileged tamper: aggregate digest alone is detected (409.978442ms)
✔ I06/PG privileged tamper: final plaintext bytes are detected (420.742268ms)
✔ I06/PG privileged tamper: final decryption-record digest is detected (415.183383ms)
✔ I06/PG roles enforce coordinator/ingester/finalizer/runtime separation (416.898593ms)
ℹ tests 22
ℹ suites 0
ℹ pass 22
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 12445.75635
✔ I07/PG crash before_result_persistence leaves no incomplete FINAL and retry converges (1167.13273ms)
✔ I07/PG crash after_result_persistence_before_evidence_publication_marker leaves no incomplete FINAL and retry converges (892.014255ms)
✔ I07/PG crash after_evidence_persistence_before_final_status_transition leaves no incomplete FINAL and retry converges (877.549656ms)
✔ I07/PG crash immediately after FINAL commit before response preserves one final result and retry is idempotent (874.656286ms)
✔ I07/PG real persistence path publishes one final bundle independently verified by A and B (1414.537263ms)
✔ I07/PG concurrent publishers converge to one immutable canonical result (774.346434ms)
✔ I07/PG idempotent retry returns same result and conflicting direct commit is rejected (720.255189ms)
✔ I07/PG least privilege: publisher has only scoped I07 write + I06 authority read; public verifier is read-only FINAL view (584.383088ms)
✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (1892.105311ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1337.291574ms)
✔ I07/PG privileged tamper aggregate bytes is detected independently of DB permissions (884.940999ms)
✔ I07/PG privileged tamper guardian public key is detected independently of DB permissions (601.883065ms)
✔ I07/PG privileged tamper threshold is detected independently of DB permissions (585.700445ms)
✔ I07/PG privileged tamper accepted share artifact is detected independently of DB permissions (593.99305ms)
✔ I07/PG privileged tamper accepted share digest is detected independently of DB permissions (604.659568ms)
✔ I07/PG privileged tamper plaintext bytes is detected independently of DB permissions (598.126552ms)
✔ I07/PG privileged tamper plaintext digest is detected independently of DB permissions (596.087212ms)
✔ I07/PG privileged tamper decryption record canonical is detected independently of DB permissions (601.146712ms)
✔ I07/PG privileged tamper public result canonical bytes is detected independently of DB permissions (727.899414ms)
✔ I07/PG privileged tamper public result digest column is detected independently of DB permissions (717.154922ms)
ℹ tests 20
ℹ suites 0
ℹ pass 20
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 17432.814575
[I10_PROGRESS] PASS label="i09:postgres-full" elapsed_ms=43750
[I10_PROGRESS] START label="i09:scale-100-1000-10000" timeout_ms=900000

> epd2-pb01-i06-candidate@0.1.0 test:i09:scale
> node scripts/i09_scale_worker.mjs 100 && node scripts/i09_scale_worker.mjs 1000 && node scripts/i09_scale_worker.mjs 10000

I09_SCALE_PROGRESS:I09-S100:setup
I09_SCALE_PROGRESS:I09-S100:ballots:943
I09_SCALE_PROGRESS:I09-S100:finalset:12
I09_SCALE_PROGRESS:I09-S100:tally:291
I09_SCALE_PROGRESS:I09-S100:decrypt:557
I09_SCALE_PROGRESS:I09-S100:evidence:7
{"schema_version":"epd2.pb01.i09-scale-result/1","fixture_id":"I09-S100","raw_submissions":110,"effective_final_set_size":100,"revote_count":10,"timings_ms":{"setup_and_credentials":165,"ballot_validation_and_generation":943,"final_set_derivation":12,"tally_computation":291,"decryption_verification":557,"result_evidence_generation":7,"independent_rust_verification":10},"result_digest":"5b8d509b619de149b6cd423718e6398b03792294f438865305adc0fee373dd6b","aggregate_digest":"ac830dc48d8d64d49c7460aae75da982e1804d7bfc0d0de722e30ea5d8924294","plaintext_tally":[["33","34","33"]],"verifier_result":{"node":"PASS","go":"PASS","rust":"PASS","byte_for_byte_agreement":true},"resource_observations":{"peak_memory":"measured externally where runner supports /usr/bin/time; no SLA claim"},"status":"PASS"}
I09_SCALE_PROGRESS:I09-S1000:setup
I09_SCALE_PROGRESS:I09-S1000:ballots:9240
I09_SCALE_PROGRESS:I09-S1000:finalset:33
I09_SCALE_PROGRESS:I09-S1000:tally:1273
I09_SCALE_PROGRESS:I09-S1000:decrypt:5002
I09_SCALE_PROGRESS:I09-S1000:evidence:38
{"schema_version":"epd2.pb01.i09-scale-result/1","fixture_id":"I09-S1000","raw_submissions":1100,"effective_final_set_size":1000,"revote_count":100,"timings_ms":{"setup_and_credentials":356,"ballot_validation_and_generation":9240,"final_set_derivation":33,"tally_computation":1273,"decryption_verification":5002,"result_evidence_generation":38,"independent_rust_verification":38},"result_digest":"4cfb13669588d5c0102c549a05f2d87f494057539c384f3eadde92e4246d1901","aggregate_digest":"1558a5c163b02961d0308c72d646b23a47f8411898117c003cc869138dad7a17","plaintext_tally":[["333","334","333"]],"verifier_result":{"node":"PASS","go":"PASS","rust":"PASS","byte_for_byte_agreement":true},"resource_observations":{"peak_memory":"measured externally where runner supports /usr/bin/time; no SLA claim"},"status":"PASS"}
I09_SCALE_PROGRESS:I09-S10000:setup
I09_SCALE_PROGRESS:I09-S10000:ballots:92136
I09_SCALE_PROGRESS:I09-S10000:finalset:262
I09_SCALE_PROGRESS:I09-S10000:tally:11143
I09_SCALE_PROGRESS:I09-S10000:decrypt:49974
I09_SCALE_PROGRESS:I09-S10000:evidence:323
{"schema_version":"epd2.pb01.i09-scale-result/1","fixture_id":"I09-S10000","raw_submissions":11000,"effective_final_set_size":10000,"revote_count":1000,"timings_ms":{"setup_and_credentials":2176,"ballot_validation_and_generation":92136,"final_set_derivation":262,"tally_computation":11143,"decryption_verification":49974,"result_evidence_generation":323,"independent_rust_verification":284},"result_digest":"7f1574dcf6b0efdc970f403d00a49ebca74ab6629567b5598e6cf492343160df","aggregate_digest":"edb07bd326d04c7cbed6bc57cf990e95d76f826e7bb1a631993dcfec00d622af","plaintext_tally":[["3333","3334","3333"]],"verifier_result":{"node":"PASS","go":"PASS","rust":"PASS","byte_for_byte_agreement":true},"resource_observations":{"peak_memory":"measured externally where runner supports /usr/bin/time; no SLA claim"},"status":"PASS"}
[I10_PROGRESS] PASS label="i09:scale-100-1000-10000" elapsed_ms=312463
[I10_PROGRESS] START label="verify:i09-agreement" timeout_ms=120000

> epd2-pb01-i06-candidate@0.1.0 verify:i09:agreement
> node scripts/i09_verify_agreement.mjs

{"schema_version":"epd2.pb01.i09-scale-agreement/2-c3","results":[{"fixture_id":"I09-S1000","byte_for_byte_agreement":true,"fields":["election_digest","final_set_reference","aggregate_digest","ceremony_digest","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]},{"fixture_id":"I09-S10000","byte_for_byte_agreement":true,"fields":["election_digest","final_set_reference","aggregate_digest","ceremony_digest","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]}],"status":"PASS"}
[I10_PROGRESS] PASS label="verify:i09-agreement" elapsed_ms=116
{
  "schema_version": "epd2.pb01.i10-final-validation/1",
  "candidate_filename": "EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C6.zip",
  "candidate_sha256": "442b83d9639a7398b3da767beb95976d379190229610d9b5ccb550d53d277d25",
  "accepted_i09_predecessor_sha256": "10e1f158a1ee621be45bf80b0f9dea21585a64ae728268affbbe41dbbc4e760a",
  "pb01_profile_id": "epd2.belenios-homomorphic/1",
  "freeze_manifest_sha256": "f70b504f23a2834680fec3defed95f1821557b2843a06811e4739dd6d0d2dced",
  "lineage_manifest_sha256": "c0ea808119be826c6b882f2f03291cf819f4b726f663e34b0b34991cde8b163a",
  "release_artifact_manifest_sha256": "51b4197adef70252d6aec70812f6dd9d922cf191cf807a3606380d04009164d6",
  "dependency_lock_digest": "df9514c2314432e613adc80f56b1a47bdc2f3143f499a1ae950c73b2649c82e0",
  "node_version": "v24.19.0",
  "go_version": "go version go1.23.2 linux/amd64",
  "rust_version": "rustc 1.97.1 (8bab26f4f 2026-07-14)",
  "cargo_version": "cargo 1.97.1 (c980f4866 2026-06-30)",
  "postgresql_version": "postgres (PostgreSQL) 16.15 (Ubuntu 16.15-1.pgdg24.04+2)",
  "rust_verifier_source_sha256": "c6f042635ef2980b6ec2514ff7e2221815b6493cd5f7d6251608eb753e6a8ad9",
  "cargo_lock_sha256": "cac1769e62290cbce862a88ea275cebb7d06f69244c94576d4ecee0c8d6aa6d7",
  "fresh_rust_executable_sha256": "9d98b894211b8ed3af7e00f1dc7ff162792c2251535b2ff6196ad363650c19b7",
  "positive_corpus_digest": "e5218bf29b1bb97e5fcc28cfb0971e2f2b686f76aa1dc44f62abaaa04234d7ce",
  "negative_corpus_digest": "abe8c6a105131aabf7b78557990ab08fec62af0c519c997aeb907a8a33dd6003",
  "scale_fixture_digest": "bdcbd6ed71f9a2a9cc7c96324bb6c37d04862f62853c6dee067239fa4ec76f1f",
  "current_run_nonce": "2d90742dda9b5513b95e9d0422d8d00e6dacdcd39738d612",
  "verification_result_digest": "0ea359b5079c172cd673b84b679e78bff435751e99c11db2ae99010aaab7b5f7",
  "validation_timeout_policy": {
    "fail_closed": true,
    "worker_total_ms": 2700000,
    "postgres_full_ms": 1200000,
    "postgres_class_ms": 600000,
    "scale_ms": 900000
  },
  "system_status": "NON_BINDING_PILOT",
  "historical_provenance_exception_count": 1,
  "historical_provenance_exception_stage": "I05",
  "release_readiness_decision": "RELEASE_READY",
  "live_execution": true,
  "status": "PASS"
}
[I10_PROGRESS] PASS label="worker:full-i10" elapsed_ms=424869
{"status":"PASS","candidate_sha256":"442b83d9639a7398b3da767beb95976d379190229610d9b5ccb550d53d277d25","clean_room":true,"timeout_policy":"FAIL_CLOSED_BOUNDED","result":"I10_FINAL_VALIDATION.json"}
```

## C6 generation tail
```text
C6_SHA256=442b83d9639a7398b3da767beb95976d379190229610d9b5ccb550d53d277d25
C6_FILE=/home/runner/work/epd2-civic-os/epd2-civic-os/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C6.zip
C6_DIFF=3_added_8_modified_0_deleted
```
