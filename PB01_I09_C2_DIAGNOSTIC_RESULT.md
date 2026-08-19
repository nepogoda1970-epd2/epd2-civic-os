# PB01-I09 C2 Diagnostic After Checker-Only Hotpatch

- Workflow run: 32297236718
- Source commit: 64e528008b233a686a02a15b4909c2aeb8003601
- Exact sealed C2 SHA256: `48fbddb686466208e4972908a3c213aa7021f4178d8bf71cc0b211f4af45ba53`
- Diagnostic modification: add already-declared `tests/i05_postgres_helpers.mjs` to predecessor checker allow-list in temporary extracted copy only.
- This run is diagnostic and cannot authorize Outcome A for C2.

**Downstream diagnostic result: FAIL — additional blocker exists.**

```text
ℹ tests 9
ℹ suites 0
ℹ pass 9
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 80.151126

> epd2-pb01-i06-candidate@0.1.0 test:i09
> node --test --test-concurrency=1 tests/i09-retry-policy.test.mjs tests/i09-static-security.test.mjs

✔ I09 retry policy is exactly bounded 40001-only with deterministic backoff (1.59514ms)
✔ retryable 40001 converges to one canonical result within budget (31.755404ms)
✔ retry budget exhaustion is explicit and bounded (61.00568ms)
✔ non-retryable database 40P01 fails immediately (0.422178ms)
✔ non-retryable database 23505 fails immediately (0.268983ms)
✔ non-retryable database 08006 fails immediately (0.185457ms)
✔ FOREIGN_ELECTION_BALLOT is never retried (0.271918ms)
✔ FINAL_SET_MISMATCH is never retried (0.149851ms)
✔ TALLY_CONFLICT is never retried (0.249286ms)
✔ unbounded or broadened retry configuration is rejected fail-closed (0.375652ms)
✔ I09 C1 single-flight coalesces same-process same-store only (51.627528ms)
✔ I09 preserves I08 Rust source, Cargo.lock and exact toolchain (6.580323ms)
✔ I09 stale I03 tally route assertion is replaced by scoped security boundary (1.551386ms)
✔ I09 retry implementation cannot retry semantic/security failures (1.280034ms)
✔ I09 required commands are registered and validate:i09 is authoritative (1.020877ms)
✔ I09 archive hygiene and predecessor manifest are governed (3.046732ms)
✔ I09 C1 validate:i09 restores full I04 predecessor regression (1.07577ms)
✔ I09 C1 DB concurrency proof cannot pass through one coalesced store transaction (0.916352ms)
✔ I09 C1 real contention proof does not count manual RAISE as burst contention (1.148526ms)
✔ I09 C1 mixed-stage races are mandatory in validator evidence (1.114573ms)
ℹ tests 20
ℹ suites 0
ℹ pass 20
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 295.707384
   Compiling version_check v0.9.5
   Compiling proc-macro2 v1.0.107
   Compiling typenum v1.20.1
   Compiling unicode-ident v1.0.24
   Compiling quote v1.0.47
   Compiling autocfg v1.5.1
   Compiling generic-array v0.14.7
   Compiling semver v1.0.28
   Compiling num-traits v0.2.19
   Compiling rustc_version v0.4.1
   Compiling serde_core v1.0.229
   Compiling curve25519-dalek v4.1.3
   Compiling serde v1.0.229
   Compiling syn v2.0.119
   Compiling cfg-if v1.0.4
   Compiling cpufeatures v0.2.17
   Compiling block-buffer v0.10.4
   Compiling crypto-common v0.1.7
   Compiling digest v0.10.7
   Compiling zeroize v1.9.0
   Compiling anyhow v1.0.86
   Compiling subtle v2.6.1
   Compiling serde_json v1.0.117
   Compiling signature v2.2.0
   Compiling ed25519 v2.2.3
   Compiling num-integer v0.1.47
   Compiling sha2 v0.10.8
   Compiling ryu v1.0.23
   Compiling itoa v1.0.18
   Compiling num-bigint v0.4.6
   Compiling curve25519-dalek-derive v0.1.1
   Compiling base64 v0.22.1
   Compiling ed25519-dalek v2.1.1
   Compiling epd2-i08-verifier-c v0.1.0 (/tmp/pb01-i09-c2-diag/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/verifier/rust)
    Finished `release` profile [optimized] target(s) in 9.46s

> epd2-pb01-i06-candidate@0.1.0 verify:i08:rust
> node scripts/i08_verify_rust.mjs positives

{"invokes_belenios":false,"invokes_go":false,"invokes_node":false,"mutation_count":"0","mutation_results":[],"mutations_rejected":"0","positive_vector_count":"4","producer_imports":false,"schema_version":"epd2.pb01.i08-rust-verifier-result/1","status":"PASS","toolchain_policy":"1.97.1","vector_results":[{"aggregate_digest":"5e295e8fd222a03b5c50d1b1bf7188620bf8db38f986f25c55a8793a2c094679","ceremony_digest":"349223d8a1a59fe480d6774df7c08912c0d2dd2df64f73ca7ec719ead0c35236","decryption_record_digest":"ab25b78657494d96c6e303242512bd8c316cc35793dfd9f838d513c33135baae","election_digest":"3a4b152f2f34b9f78318619b64c5d282d5d497ba9cb3a01618fadac6162d3d27","final_set_reference":"4d33ca52ac94a90c22049dc017e7a69a53dbbd7211308c54722383d6753605d1","plaintext_tally_digest":"580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c","public_evidence_bundle_digest":"d15194b1bb5c8ad10e8cf9402c9c8b1dcd0fc575597f583e5121c70b712fa0cc","public_result_digest":"550ed2b41b465f71b615ce3805cfb884a2f6d16f9780b8bad96694a5718b001e","share_digests":["e56f69730ed30a8530a78352d861f937a76d12cd8996d9c0f1641bd067da24f7","ef5fee15828ba66192a6f2480edd8ba83a61361fd3da8bd76b9f640ff0aa6d40"],"status":"PASS","vector_id":"I07-V01"},{"aggregate_digest":"5e295e8fd222a03b5c50d1b1bf7188620bf8db38f986f25c55a8793a2c094679","ceremony_digest":"349223d8a1a59fe480d6774df7c08912c0d2dd2df64f73ca7ec719ead0c35236","decryption_record_digest":"ab25b78657494d96c6e303242512bd8c316cc35793dfd9f838d513c33135baae","election_digest":"3a4b152f2f34b9f78318619b64c5d282d5d497ba9cb3a01618fadac6162d3d27","final_set_reference":"4d33ca52ac94a90c22049dc017e7a69a53dbbd7211308c54722383d6753605d1","plaintext_tally_digest":"580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c","public_evidence_bundle_digest":"1466f5c6479911da060f642d4fba08424703c7380d4aa2cb154be315d2d6f2da","public_result_digest":"550ed2b41b465f71b615ce3805cfb884a2f6d16f9780b8bad96694a5718b001e","share_digests":["e56f69730ed30a8530a78352d861f937a76d12cd8996d9c0f1641bd067da24f7","ef5fee15828ba66192a6f2480edd8ba83a61361fd3da8bd76b9f640ff0aa6d40","d19e010be386dd735c96a0ba444aabbea6d6d5865227c3e01f1dd26860b34d4b"],"status":"PASS","vector_id":"I07-V02"},{"aggregate_digest":"5e295e8fd222a03b5c50d1b1bf7188620bf8db38f986f25c55a8793a2c094679","ceremony_digest":"349223d8a1a59fe480d6774df7c08912c0d2dd2df64f73ca7ec719ead0c35236","decryption_record_digest":"ab25b78657494d96c6e303242512bd8c316cc35793dfd9f838d513c33135baae","election_digest":"3a4b152f2f34b9f78318619b64c5d282d5d497ba9cb3a01618fadac6162d3d27","final_set_reference":"4d33ca52ac94a90c22049dc017e7a69a53dbbd7211308c54722383d6753605d1","plaintext_tally_digest":"580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c","public_evidence_bundle_digest":"1466f5c6479911da060f642d4fba08424703c7380d4aa2cb154be315d2d6f2da","public_result_digest":"550ed2b41b465f71b615ce3805cfb884a2f6d16f9780b8bad96694a5718b001e","share_digests":["e56f69730ed30a8530a78352d861f937a76d12cd8996d9c0f1641bd067da24f7","ef5fee15828ba66192a6f2480edd8ba83a61361fd3da8bd76b9f640ff0aa6d40","d19e010be386dd735c96a0ba444aabbea6d6d5865227c3e01f1dd26860b34d4b"],"status":"PASS","vector_id":"I07-V03"},{"aggregate_digest":"7e6beffefc73c8103d2dab246bce4651a9bcc5330b081a533cadc6b792c45837","ceremony_digest":"56f267a4f7b97af768eb4b77ab108bf5b4a4ae7ffa351bd893c801363889d304","decryption_record_digest":"6cab8be2cf8f4db1024d1ba78168924b74f77f1008cc18b855b44b3c1c03e8ad","election_digest":"b99461b29f37a7ccc4c1022f88bd7add2fe61482fa7c3a276c4aaf5348367955","final_set_reference":"3de669d8adc92f417919af7d9ba9691945a83e5171844d34c15a49805d6243d6","plaintext_tally_digest":"34ed65c6fe5fe649af9223803d39b30259c000b9f5605503a39c7259ab7eedda","public_evidence_bundle_digest":"2f9ac3d8805b27941c35918f663dde7a17f12a49fe22a7f106319d991e871748","public_result_digest":"2b1de73c9d19a3bdaa9cd2248e440dd4ae40f7c50f9e01fbbb3db87fdb8f6978","share_digests":["5e4a20157d368cdbf66fea465e53886a01f6710aa0915e19f2cd38b4b82cccec","81d81fe34a500c186c2a68d2337fcb029c994951d46b74e30a7afae05a5435b1"],"status":"PASS","vector_id":"I07-V04"}],"verifier":"independent-rust-verifier-c"}

> epd2-pb01-i06-candidate@0.1.0 verify:i08:rust:negatives
> node scripts/i08_verify_rust.mjs negatives

{"invokes_belenios":false,"invokes_go":false,"invokes_node":false,"mutation_count":"26","mutation_results":[{"mutation_id":"I07-N01","reason":"I07_ELECTION_CROSS_BIND","status":"REJECT"},{"mutation_id":"I07-N02","reason":"I07_ELECTION_CROSS_BIND","status":"REJECT"},{"mutation_id":"I07-N03","reason":"I06_RECORD_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N04","reason":"I07_FINAL_SET_CROSS_BIND","status":"REJECT"},{"mutation_id":"I07-N05","reason":"I05_EVIDENCE_DIGEST","status":"REJECT"},{"mutation_id":"I07-N06","reason":"I05_EVIDENCE_DIGEST","status":"REJECT"},{"mutation_id":"I07-N07","reason":"I06_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N08","reason":"I06_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N09","reason":"I06_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N10","reason":"I06_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N11","reason":"I06_DUPLICATE_GUARDIAN","status":"REJECT"},{"mutation_id":"I07-N12","reason":"I08_SHARE_RAW_JSON","status":"REJECT"},{"mutation_id":"I07-N13","reason":"GROUP_POINT_INVALID","status":"REJECT"},{"mutation_id":"I07-N14","reason":"I08_PARTIAL_DECRYPTION_PROOF","status":"REJECT"},{"mutation_id":"I07-N15","reason":"I06_SHARE_DIGEST","status":"REJECT"},{"mutation_id":"I07-N16","reason":"I06_THRESHOLD_MEMBERSHIP","status":"REJECT"},{"mutation_id":"I07-N17","reason":"I06_RECORD","status":"REJECT"},{"mutation_id":"I07-N18","reason":"I06_RECORD","status":"REJECT"},{"mutation_id":"I07-N19","reason":"I06_RECORD","status":"REJECT"},{"mutation_id":"I07-N20","reason":"I06_RECORD","status":"REJECT"},{"mutation_id":"I07-N21","reason":"I07_RESULT_BIND","status":"REJECT"},{"mutation_id":"I07-N22","reason":"I07_ELECTION_CROSS_BIND","status":"REJECT"},{"mutation_id":"I07-N23","reason":"I07_RESULT_BIND","status":"REJECT"},{"mutation_id":"I07-N24","reason":"I06_RECORD_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N25","reason":"FIELD_REQUIRED:i06_accepted_partial_decryption_shares","status":"REJECT"},{"mutation_id":"I07-N26","reason":"I07_SCHEMA","status":"REJECT"}],"mutations_rejected":"26","positive_vector_count":"0","producer_imports":false,"schema_version":"epd2.pb01.i08-rust-verifier-result/1","status":"PASS","toolchain_policy":"1.97.1","vector_results":[],"verifier":"independent-rust-verifier-c"}

> epd2-pb01-i06-candidate@0.1.0 verify:i08:agreement
> node scripts/i08_cross_language_agreement.mjs

{"schema_version":"epd2.pb01.i08-node-go-rust-agreement/1","run_nonce":"f1831803312b3deac9534053de0d04da","verifier_a":"independent-node-verifier-a","verifier_b":"independent-go-verifier-b","verifier_c":"independent-rust-verifier-c","rust_executable":{"path":"/tmp/pb01-i09-c2-diag/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/verifier/rust/target/release/epd2-i08-verifier-c","class":"fresh_build","sha256":"9f22d6f74af6648f7329963478fcf1d391d450ee23ef19d7d5c8a96a2999f775"},"live_recomputed":true,"vector_count":"4","vector_results":[{"vector_id":"I07-V01","byte_for_byte_agreement":true,"fields":["status","election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]},{"vector_id":"I07-V02","byte_for_byte_agreement":true,"fields":["status","election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]},{"vector_id":"I07-V03","byte_for_byte_agreement":true,"fields":["status","election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]},{"vector_id":"I07-V04","byte_for_byte_agreement":true,"fields":["status","election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]}],"byte_for_byte_agreement":true,"status":"PASS"}

> epd2-pb01-i06-candidate@0.1.0 test:i09:concurrency
> bash scripts/run_i09_c1_concurrency.sh

✔ I09 C1/PG 16 execute callers use 16 independent stores/DB transactions and converge (337.189929ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 455.300326
✔ I09 C1/PG 8 execute callers use 8 independent stores/DB transactions and converge (318.325785ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 436.995181
✔ I09 C1/PG 4 execute callers use 4 independent stores/DB transactions and converge (305.596588ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 429.462814
✔ I09 C1/PG 2 execute callers use 2 independent stores/DB transactions and converge (298.861982ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 418.289009
✔ I09/PG deterministic injected 40001 remains a retry-policy test only (317.18633ms)
✔ I09/PG retry budget exhausted produces explicit operational failure and no tally (275.342837ms)
✔ I09/PG non-retryable database SQLSTATE fails immediately (189.886285ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 901.342426
✔ I09 C1/PG burst produces 40001 from real concurrent SERIALIZABLE transactions and converges (319.719239ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 440.283777
✔ I09 C1 mixed A: tally during uncommitted finalization fails closed, retry after commit yields one canonical tally (277.300673ms)
✔ I09 C1 mixed B: publication cannot cross an uncommitted decryption boundary (1071.767515ms)
✔ I09 C1 mixed C: read-only verifier sees no bundle during publication transaction, then complete canonical bundle PASS (847.722649ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2338.326418
{"status":"C1_CONCURRENCY_AND_MIXED_PASS","postgresql_version":"postgres (PostgreSQL) 16.14 (Ubuntu 16.14-1.pgdg24.04+1)"}

> epd2-pb01-i06-candidate@0.1.0 test:i09:crash
> bash scripts/run_i09_postgres_class.sh tests/i05-postgres-crash-restart.test.mjs tests/i06-postgres-concurrency-crash.test.mjs tests/i07-postgres-crash.test.mjs

✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (801.350961ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (590.978053ms)
✔ I06/PG concurrent final threshold shares converge to one immutable record (1047.303997ms)
✔ I06/PG same-guardian concurrent duplicate race never double-counts threshold (340.079786ms)
✔ I06/PG CRASH-01 retry deterministically converges (769.594861ms)
✔ I06/PG CRASH-02 retry deterministically converges (629.45103ms)
✔ I06/PG CRASH-03 retry deterministically converges (760.519973ms)
✔ I06/PG CRASH-04 retry deterministically converges (653.899667ms)
✔ I07/PG crash before_result_persistence leaves no incomplete FINAL and retry converges (1470.290531ms)
✔ I07/PG crash after_result_persistence_before_evidence_publication_marker leaves no incomplete FINAL and retry converges (1105.317771ms)
✔ I07/PG crash after_evidence_persistence_before_final_status_transition leaves no incomplete FINAL and retry converges (1064.130896ms)
✔ I07/PG crash immediately after FINAL commit before response preserves one final result and retry is idempotent (1092.249646ms)
ℹ tests 12
ℹ suites 0
ℹ pass 12
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 10683.149804

> epd2-pb01-i06-candidate@0.1.0 test:i09:restart
> bash scripts/run_i09_postgres_class.sh tests/i05-postgres-crash-restart.test.mjs tests/i06-postgres-restart-backup.test.mjs tests/i07-postgres-restart-backup.test.mjs

✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (814.289748ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (586.196251ms)
✔ I06/PG hard database crash/restart preserves same immutable plaintext and record digest (1206.795611ms)
✔ I06/PG backup/restore preserves exact public ceremony/share/decryption evidence and no private guardian columns exist (893.918116ms)
✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (1884.787305ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1522.227065ms)
ℹ tests 6
ℹ suites 0
ℹ pass 6
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 7255.882434

> epd2-pb01-i06-candidate@0.1.0 test:i09:backup-restore
> bash scripts/run_i09_postgres_class.sh tests/i07-postgres-restart-backup.test.mjs

✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (1912.400302ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1509.756708ms)
ℹ tests 2
ℹ suites 0
ℹ pass 2
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3544.732924

> epd2-pb01-i06-candidate@0.1.0 test:i09:postgres
> I09_PG_STAGE=i03 bash scripts/run_i09_postgres_class.sh tests/postgres.integration.test.mjs tests/postgres-crash-concurrency.test.mjs tests/postgres-tamper-backup-roles.test.mjs && I09_PG_STAGE=i04 bash scripts/run_i09_postgres_class.sh tests/i04-finalization.integration.test.mjs tests/i04-concurrency-crash.test.mjs tests/i04-tamper-backup-roles.test.mjs && I09_PG_STAGE=i05 bash scripts/run_i09_postgres_class.sh tests/i05-postgres.integration.test.mjs tests/i05-postgres-runtime.test.mjs tests/i05-postgres-crash-restart.test.mjs tests/i05-postgres-tamper-backup-roles.test.mjs && I09_PG_STAGE=i06 bash scripts/run_i09_postgres_class.sh tests/i06-postgres-ceremony-decryption.test.mjs tests/i06-postgres-concurrency-crash.test.mjs tests/i06-postgres-restart-backup.test.mjs tests/i06-postgres-tamper-roles.test.mjs && I09_PG_STAGE=i07 bash scripts/run_i09_postgres_class.sh tests/i07-postgres-publication.test.mjs tests/i07-postgres-crash.test.mjs tests/i07-postgres-tamper.test.mjs tests/i07-postgres-restart-backup.test.mjs

✔ PG concurrent same key and same digest create one logical acceptance (184.804431ms)
✔ PG concurrent legitimate revotes coexist under one private lifecycle (93.946025ms)
✔ PG CRASH-01 after crypto before transaction leaves no accepted state (64.355406ms)
✔ PG CRASH-02/04 committed response loss survives service restart and retry (95.669331ms)
✔ PG CRASH-03 client disconnect cannot lose a committed acceptance (95.260686ms)
✔ PG append-only triggers and hash-chain checkpoint detect privileged tampering (189.007513ms)
✔ PG backup/restore preserves exact bytes, receipt state, ledger and private/public split (232.021705ms)
✔ PG submission runtime and evidence reader have no DDL or mutation authority (73.838046ms)
✔ PG-I03-P01 real I02 ballot follows native verification and PostgreSQL acceptance (139.029266ms)
✔ PG-I03-P02 idempotent retry returns same receipt; same key with different ballot conflicts (140.17489ms)
ℹ tests 10
ℹ suites 0
ℹ pass 10
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1608.239474
✔ I04 concurrent identical and conflicting finalizers converge without split state (212.727853ms)
✔ I04-CRASH-01 is atomic and retry converges (139.789794ms)
✔ I04-CRASH-02 is atomic and retry converges (130.793859ms)
✔ I04-CRASH-03 is atomic and retry converges (129.111971ms)
✔ I04-CRASH-04 is atomic and retry converges (123.504966ms)
✔ I04 submission-versus-closure race has one deterministic boundary outcome (144.112204ms)
✔ I04 real I03 revote E2E selects latest valid, preserves history and exact bytes (262.440186ms)
✔ I04 multi-lifecycle resolution yields A2, B1 and C3 in I01 digest order (256.258132ms)
✔ I04 empty election finalizes deterministically (94.985048ms)
✔ I04 public verifier detects every committed-field tamper class (239.862633ms)
✔ I04 refuses finalization when I03 ledger integrity has been altered (122.028388ms)
✔ I04 PostgreSQL roles enforce submission/finalizer/evidence/migration separation (174.408943ms)
✔ I04 backup/restore preserves exact I03 history and identical final artifacts (389.026214ms)
ℹ tests 13
ℹ suites 0
ℹ pass 13
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2739.285527
✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (797.217293ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (598.248853ms)
✔ I05/PG exact finalized I04 set becomes the tally input and native Belenios re-verification runs per ballot (291.391638ms)
✔ I05/PG idempotent retry replays one physical tally without recomputing a second record (276.246385ms)
✔ I05/PG concurrent tally executions never diverge and every caller converges on one identical tally (201.775451ms)
✔ I05/PG rejects a conflicting F_final and a conflicting tally record against the same election (236.070919ms)
✔ I05/PG recompute reproduces the committed tally byte-for-byte from PostgreSQL state (261.520928ms)
✔ I05/PG append-only triggers reject mutation of committed tally state even for the schema owner (293.089159ms)
✔ I05/PG privileged tamper that bypasses the triggers is still detected by evidence and recompute (291.417958ms)
✔ I05/PG tally runtime cannot mutate I03 or I04 state (202.405754ms)
✔ I05/PG submission, finalizer and evidence roles cannot mutate I05 tally state (233.109725ms)
✔ I05/PG tally and evidence roles hold no DDL or TEMP privilege anywhere (199.288815ms)
✔ I05/PG backup and restore preserve exact aggregate and tally bytes and every digest (436.571872ms)
✔ I05 PostgreSQL exact finalized set tally, idempotency, recompute, concurrency and privileges (370.910387ms)
✔ I05 PostgreSQL CRASH-03 rolls aggregate insert back; retry converges (234.456379ms)
ℹ tests 15
ℹ suites 0
ℹ pass 15
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 5366.877121
✔ I06/PG real threshold ceremony freezes immutable N=3 T=2 public context (589.043798ms)
✔ I06/PG T-1 exposes no plaintext; exact threshold commits one immutable result; extra valid share cannot change plaintext (857.592678ms)
✔ I06/PG duplicate guardian and malformed/invalid share fail closed (511.496058ms)
✔ I06/PG concurrent final threshold shares converge to one immutable record (1030.53957ms)
✔ I06/PG same-guardian concurrent duplicate race never double-counts threshold (346.169037ms)
✔ I06/PG CRASH-01 retry deterministically converges (783.292875ms)
✔ I06/PG CRASH-02 retry deterministically converges (641.556672ms)
✔ I06/PG CRASH-03 retry deterministically converges (773.494117ms)
✔ I06/PG CRASH-04 retry deterministically converges (641.156293ms)
✔ I06/PG hard database crash/restart preserves same immutable plaintext and record digest (1311.145651ms)
✔ I06/PG backup/restore preserves exact public ceremony/share/decryption evidence and no private guardian columns exist (895.192347ms)
✔ I06/PG mandatory I05 corrective detects privileged aggregate-byte-only rewrite and decryption refuses (985.024116ms)
✔ I06/PG privileged tamper: guardian public key after freeze is detected (520.067999ms)
✔ I06/PG privileged tamper: threshold after ceremony freeze is detected (498.597177ms)
✔ I06/PG privileged tamper: frozen guardian-set member replacement is detected (508.142986ms)
✔ I06/PG privileged tamper: partial-decryption factor bytes are detected (507.243432ms)
✔ I06/PG privileged tamper: partial-decryption proof bytes are detected (512.416877ms)
✔ I06/PG privileged tamper: accepted share digest column is detected (517.880413ms)
✔ I06/PG privileged tamper: aggregate digest alone is detected (502.28392ms)
✔ I06/PG privileged tamper: final plaintext bytes are detected (522.010122ms)
✔ I06/PG privileged tamper: final decryption-record digest is detected (509.700981ms)
✔ I06/PG roles enforce coordinator/ingester/finalizer/runtime separation (499.569188ms)
ℹ tests 22
ℹ suites 0
ℹ pass 22
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 14944.451777
✔ I07/PG crash before_result_persistence leaves no incomplete FINAL and retry converges (1458.771022ms)
✔ I07/PG crash after_result_persistence_before_evidence_publication_marker leaves no incomplete FINAL and retry converges (1091.001302ms)
✔ I07/PG crash after_evidence_persistence_before_final_status_transition leaves no incomplete FINAL and retry converges (1066.925683ms)
✔ I07/PG crash immediately after FINAL commit before response preserves one final result and retry is idempotent (1081.887835ms)
✔ I07/PG real persistence path publishes one final bundle independently verified by A and B (1682.775718ms)
✔ I07/PG concurrent publishers converge to one immutable canonical result (972.50012ms)
✔ I07/PG idempotent retry returns same result and conflicting direct commit is rejected (901.081661ms)
✔ I07/PG least privilege: publisher has only scoped I07 write + I06 authority read; public verifier is read-only FINAL view (729.789343ms)
✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (2004.411116ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1507.154463ms)
✔ I07/PG privileged tamper aggregate bytes is detected independently of DB permissions (1064.417496ms)
✔ I07/PG privileged tamper guardian public key is detected independently of DB permissions (734.229175ms)
✔ I07/PG privileged tamper threshold is detected independently of DB permissions (722.582184ms)
✔ I07/PG privileged tamper accepted share artifact is detected independently of DB permissions (734.227498ms)
✔ I07/PG privileged tamper accepted share digest is detected independently of DB permissions (748.317641ms)
✔ I07/PG privileged tamper plaintext bytes is detected independently of DB permissions (738.413634ms)
✔ I07/PG privileged tamper plaintext digest is detected independently of DB permissions (741.169692ms)
✔ I07/PG privileged tamper decryption record canonical is detected independently of DB permissions (751.399046ms)
✔ I07/PG privileged tamper public result canonical bytes is detected independently of DB permissions (890.896438ms)
✔ I07/PG privileged tamper public result digest column is detected independently of DB permissions (868.029065ms)
ℹ tests 20
ℹ suites 0
ℹ pass 20
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 20981.409329
{"status":"PASS","postgresql_version":"postgres (PostgreSQL) 16.14 (Ubuntu 16.14-1.pgdg24.04+1)"}

> epd2-pb01-i06-candidate@0.1.0 test:i09:scale
> node scripts/i09_scale_worker.mjs 100 && node scripts/i09_scale_worker.mjs 1000 && node scripts/i09_scale_worker.mjs 10000

I09_SCALE_PROGRESS:I09-S100:setup
I09_SCALE_PROGRESS:I09-S100:ballots:1155
I09_SCALE_PROGRESS:I09-S100:finalset:15
I09_SCALE_PROGRESS:I09-S100:tally:358
I09_SCALE_PROGRESS:I09-S100:decrypt:677
I09_SCALE_PROGRESS:I09-S100:evidence:7
{"schema_version":"epd2.pb01.i09-scale-result/1","fixture_id":"I09-S100","raw_submissions":110,"effective_final_set_size":100,"revote_count":10,"timings_ms":{"setup_and_credentials":204,"ballot_validation_and_generation":1155,"final_set_derivation":15,"tally_computation":358,"decryption_verification":677,"result_evidence_generation":7,"independent_rust_verification":11},"result_digest":"fd32ed5687b661ff21b637a858969219db06060719b80ce976f2d20750eae7b0","aggregate_digest":"90da671c3655441039622c231f67341365ae0357e462775bc6b3ffa1429bbe86","plaintext_tally":[["33","34","33"]],"verifier_result":{"node":"PASS","go":"PASS","rust":"PASS","byte_for_byte_agreement":true},"resource_observations":{"peak_memory":"measured externally where runner supports /usr/bin/time; no SLA claim"},"status":"PASS"}
I09_SCALE_PROGRESS:I09-S1000:setup
I09_SCALE_PROGRESS:I09-S1000:ballots:11275
I09_SCALE_PROGRESS:I09-S1000:finalset:44
I09_SCALE_PROGRESS:I09-S1000:tally:1630
I09_SCALE_PROGRESS:I09-S1000:decrypt:6048
I09_SCALE_PROGRESS:I09-S1000:evidence:50
{"schema_version":"epd2.pb01.i09-scale-result/1","fixture_id":"I09-S1000","raw_submissions":1100,"effective_final_set_size":1000,"revote_count":100,"timings_ms":{"setup_and_credentials":480,"ballot_validation_and_generation":11275,"final_set_derivation":44,"tally_computation":1630,"decryption_verification":6048,"result_evidence_generation":50,"independent_rust_verification":44},"result_digest":"85987341a91190f6a2762d2759529c69c78b92e18e8e41af85b25205a8dcfa8b","aggregate_digest":"ed42b17fbb9df8a483428594235785dc8f307719fdb324a06bea75159b51727d","plaintext_tally":[["333","334","333"]],"verifier_result":{"node":"PASS","go":"PASS","rust":"PASS","byte_for_byte_agreement":true},"resource_observations":{"peak_memory":"measured externally where runner supports /usr/bin/time; no SLA claim"},"status":"PASS"}
I09_SCALE_PROGRESS:I09-S10000:setup
I09_SCALE_PROGRESS:I09-S10000:ballots:112647
I09_SCALE_PROGRESS:I09-S10000:finalset:335
I09_SCALE_PROGRESS:I09-S10000:tally:13964
I09_SCALE_PROGRESS:I09-S10000:decrypt:60546
I09_SCALE_PROGRESS:I09-S10000:evidence:448
{"schema_version":"epd2.pb01.i09-scale-result/1","fixture_id":"I09-S10000","raw_submissions":11000,"effective_final_set_size":10000,"revote_count":1000,"timings_ms":{"setup_and_credentials":3175,"ballot_validation_and_generation":112647,"final_set_derivation":335,"tally_computation":13964,"decryption_verification":60546,"result_evidence_generation":448,"independent_rust_verification":340},"result_digest":"132a3bdb1235e241083636cb4dae47dbf5a5a03ec63c05936a839ab133cc9601","aggregate_digest":"6687e9b83f32c9fc1a8220f6aed8d2f39accf51ea974d8370a5509376ff3e157","plaintext_tally":[["3333","3334","3333"]],"verifier_result":{"node":"PASS","go":"PASS","rust":"PASS","byte_for_byte_agreement":true},"resource_observations":{"peak_memory":"measured externally where runner supports /usr/bin/time; no SLA claim"},"status":"PASS"}

> epd2-pb01-i06-candidate@0.1.0 verify:i09:agreement
> node scripts/i09_verify_agreement.mjs

file:///tmp/pb01-i09-c2-diag/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/scripts/i09_verify_agreement.mjs:3
const out=[];for(const n of [1000,10000]){const d=`evidence/results/i09/scale/I09-S${n}`;const [node,go,rust,scale]=await Promise.all([readFile(`${d}/node.json`,'utf8').then(JSON.parse),readFile(`${d}/go.json`,'utf8').then(JSON.parse),readFile(`${d}/rust.json`,'utf8').then(JSON.parse),readFile(`${d}/scale-result.json`,'utf8').then(JSON.parse)]);const ok=fields.every(k=>node[k]===go[k]&&node[k]===rust[k]);if(!ok||scale.status!=='PASS')throw new Error(`I09_SCALE_AGREEMENT_FAIL:${n}`);out.push({fixture_id:`I09-S${n}`,byte_for_byte_agreement:true,fields});}
                                                                                                                                                                                                                                                                                                                                                                                                                                                            ^

Error: I09_SCALE_AGREEMENT_FAIL:1000
    at file:///tmp/pb01-i09-c2-diag/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/scripts/i09_verify_agreement.mjs:3:445

Node.js v24.19.0
file:///tmp/pb01-i09-c2-diag/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/scripts/i09_validate_current_run.mjs:28
      : rejectRun(Object.assign(new Error(`${cmd} ${args.join(' ')} exit ${code}: ${Buffer.concat(err).toString().slice(-4000)}`), { exitCode: code })));
                                ^

Error: npm run verify:i09:agreement exit 1: file:///tmp/pb01-i09-c2-diag/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/scripts/i09_verify_agreement.mjs:3
const out=[];for(const n of [1000,10000]){const d=`evidence/results/i09/scale/I09-S${n}`;const [node,go,rust,scale]=await Promise.all([readFile(`${d}/node.json`,'utf8').then(JSON.parse),readFile(`${d}/go.json`,'utf8').then(JSON.parse),readFile(`${d}/rust.json`,'utf8').then(JSON.parse),readFile(`${d}/scale-result.json`,'utf8').then(JSON.parse)]);const ok=fields.every(k=>node[k]===go[k]&&node[k]===rust[k]);if(!ok||scale.status!=='PASS')throw new Error(`I09_SCALE_AGREEMENT_FAIL:${n}`);out.push({fixture_id:`I09-S${n}`,byte_for_byte_agreement:true,fields});}
                                                                                                                                                                                                                                                                                                                                                                                                                                                            ^

Error: I09_SCALE_AGREEMENT_FAIL:1000
    at file:///tmp/pb01-i09-c2-diag/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/scripts/i09_verify_agreement.mjs:3:445

Node.js v24.19.0

    at ChildProcess.<anonymous> (file:///tmp/pb01-i09-c2-diag/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/scripts/i09_validate_current_run.mjs:28:33)
    at ChildProcess.emit (node:events:509:28)
    at ChildProcess._handle.onexit (node:internal/child_process:295:12) {
  exitCode: 1
}

Node.js v24.19.0
```
