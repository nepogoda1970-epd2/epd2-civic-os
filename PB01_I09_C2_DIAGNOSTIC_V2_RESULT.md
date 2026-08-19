# PB01-I09 C2 Diagnostic v2 After Two Harness-Only Hotpatches

- Workflow run: 32298264998
- Source commit: 188d4aea9033e5e19680cbc856d0e8204b2a1145
- Exact sealed C2 SHA256: `48fbddb686466208e4972908a3c213aa7021f4178d8bf71cc0b211f4af45ba53`
- Diagnostic hotpatch 1: add declared `tests/i05_postgres_helpers.mjs` to predecessor allow-list.
- Diagnostic hotpatch 2: normalize Go/Rust single-result wrappers via `vector_results[0]` before governed-field agreement comparison.
- This run cannot authorize Outcome A for C2.

**Downstream diagnostic result: FAIL — an additional blocker remains.**

```text
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 5217.96981

> epd2-pb01-i06-candidate@0.1.0 test:i04:verifier-b
> node --test tests/i04-cross-language-verifier.test.mjs

✔ I04 independent cross-language Verifier B consumes all frozen vectors and rejects required mutations (3501.356811ms)
✔ independent verifier source does not import producer hashing/canonicalization modules (1.474811ms)
ℹ tests 2
ℹ suites 0
ℹ pass 2
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3547.043428

> epd2-pb01-i06-candidate@0.1.0 test:i05
> node --test --test-concurrency=1 tests/i05-vectors.test.mjs tests/i05-api-boundary.test.mjs tests/i05-static-security.test.mjs tests/i05-crash-concurrency.test.mjs

✔ tally API accepts only election reference in path and rejects caller ballot arrays (35.334323ms)
✔ CRASH-01..04 retry converges and same tally concurrency is one logical record (398.747028ms)
✔ I05 adds no decryption/guardian secret material and SQL enforces role separation (6.914521ms)
✔ I05 real Belenios vectors and both verifier reports pass (4.151611ms)
✔ revote vector consumes only A2/B1/C3 and agrees with independent three-ballot aggregate (1.344695ms)
✔ empty final set has deterministic upstream identity aggregate (1.743134ms)
✔ real alternate aggregates and foreign ballot attacks are rejected (0.769418ms)
✔ independently encrypted/revoted ciphertexts remain distinct exact ballots (0.641185ms)
ℹ tests 8
ℹ suites 0
ℹ pass 8
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 671.750698

> epd2-pb01-i06-candidate@0.1.0 test:i06
> node --test --test-concurrency=1 tests/i06-i05-corrective.test.mjs tests/i06-vectors.test.mjs tests/i06-mutation-vectors.test.mjs tests/i06-threshold-negatives.test.mjs tests/i06-api-boundary.test.mjs tests/i06-static-security.test.mjs

✔ I06 API never accepts caller-selected aggregate/ciphertext input (30.030397ms)
✔ I05 corrective recomputes digest from persisted aggregate bytes and I06 refuses byte-only mutation before ceremony access (98.346276ms)
✔ stale/unauthorized I05 tally cannot enter guardian/decryption path (0.315405ms)
✔ I06-N01 frozen mutation vector rejects (4.052291ms)
✔ I06-N02 frozen mutation vector rejects (1.061829ms)
✔ I06-N03 frozen mutation vector rejects (0.843409ms)
✔ I06-N04 frozen mutation vector rejects (32.988707ms)
✔ I06-N05 frozen mutation vector rejects (32.155537ms)
✔ I06-N06 frozen mutation vector rejects (29.576284ms)
✔ I06-N07 frozen mutation vector rejects (0.799554ms)
✔ I06-N08 frozen mutation vector rejects (0.939941ms)
✔ I06-N09 frozen mutation vector rejects (0.588386ms)
✔ candidate contains no guardian private key material or decryption/admin secret API (57.904177ms)
✔ I06 source has no plaintext result before threshold API route and no arbitrary aggregate input surface (0.951838ms)
✔ mutation negatives: wrong aggregate/election/guardian/digests/plaintext/record fail closed (2.172041ms)
✔ T-1 share has no Belenios plaintext result (27.06326ms)
✔ invalid proof among threshold shares is rejected by pinned upstream Belenios (31.518368ms)
✔ duplicate guardian cannot form threshold (29.932119ms)
✔ I06-V01 real Belenios threshold vector verifies (111.333296ms)
✔ I06-V02 real Belenios threshold vector verifies (151.357255ms)
✔ I06-V03 real Belenios threshold vector verifies (150.614848ms)
✔ I06-V04 real Belenios threshold vector verifies (91.897181ms)
✔ N=5 T=3 different valid threshold subsets and all five give identical plaintext (199.116797ms)
ℹ tests 23
ℹ suites 0
ℹ pass 23
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1513.090748

> epd2-pb01-i06-candidate@0.1.0 test:i07
> node --test --test-concurrency=1 tests/i07-vectors.test.mjs tests/i07-mutations.test.mjs tests/i07-offline.test.mjs tests/i07-static-security.test.mjs tests/i07-validation-harness.test.mjs

✔ Verifier A rejects all 26 frozen mutations (199.987774ms)
✔ mutation index is complete and unique (0.196966ms)
✔ I07 downloaded frozen bundle verifies offline with independent Verifier A (146.693183ms)
✔ I07 downloaded frozen bundle verifies offline with independent Go Verifier B (2794.391387ms)
✔ I07 public bundles contain no identity/private/analytics fields and remain NON_BINDING_PILOT (5.690608ms)
✔ I07 code introduces no universal authority and no guardian private-key files (129.939026ms)
✔ stale packaged PostgreSQL acceptance cannot satisfy a new validation invocation (1.446838ms)
✔ tampered PostgreSQL attestation binding is rejected (0.196335ms)
✔ current invocation 20/20 PostgreSQL 16 + exact Node attestation is accepted (0.662477ms)
✔ I07-V01 producer structural public bundle verification (5.954946ms)
✔ I07-V02 producer structural public bundle verification (2.619544ms)
✔ I07-V03 producer structural public bundle verification (5.674174ms)
✔ I07-V04 producer structural public bundle verification (1.936535ms)
✔ V01/V02/V03 publish byte-identical deterministic result (1.157203ms)
✔ V04 is deterministic zero tally (1.48783ms)
ℹ tests 15
ℹ suites 0
ℹ pass 15
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3507.332185

> epd2-pb01-i06-candidate@0.1.0 test:i08
> node --test --test-concurrency=1 tests/i08-release-hardening.test.mjs

✔ I08 exact Rust dependency declarations and pinned toolchain (4.721389ms)
✔ Cargo.lock and vendored offline closure are committed and governed (1.798408ms)
✔ I08 frozen positive and negative corpus remains 4 / 26 (1.486808ms)
✔ Rust verifier has no Node/Go/Belenios process execution dependency (0.86945ms)
✔ release hygiene fails closed on tmp and temporary leftovers (0.31227ms)
✔ validate:i08 pins exact Node and authorizes only fresh Rust build (1.141149ms)
✔ I08 commands are registered (0.777086ms)
✔ I08 verifier/release changes do not expand authority (1.309632ms)
✔ release profile fixes source, lock, toolchain and vector-set provenance (0.941909ms)
ℹ tests 9
ℹ suites 0
ℹ pass 9
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 62.844385

> epd2-pb01-i06-candidate@0.1.0 test:i09
> node --test --test-concurrency=1 tests/i09-retry-policy.test.mjs tests/i09-static-security.test.mjs

✔ I09 retry policy is exactly bounded 40001-only with deterministic backoff (1.145645ms)
✔ retryable 40001 converges to one canonical result within budget (31.555343ms)
✔ retry budget exhaustion is explicit and bounded (61.536466ms)
✔ non-retryable database 40P01 fails immediately (0.41141ms)
✔ non-retryable database 23505 fails immediately (0.280162ms)
✔ non-retryable database 08006 fails immediately (0.206771ms)
✔ FOREIGN_ELECTION_BALLOT is never retried (0.201694ms)
✔ FINAL_SET_MISMATCH is never retried (0.108323ms)
✔ TALLY_CONFLICT is never retried (0.163206ms)
✔ unbounded or broadened retry configuration is rejected fail-closed (0.317578ms)
✔ I09 C1 single-flight coalesces same-process same-store only (51.400213ms)
✔ I09 preserves I08 Rust source, Cargo.lock and exact toolchain (4.623441ms)
✔ I09 stale I03 tally route assertion is replaced by scoped security boundary (1.100176ms)
✔ I09 retry implementation cannot retry semantic/security failures (0.920857ms)
✔ I09 required commands are registered and validate:i09 is authoritative (0.656669ms)
✔ I09 archive hygiene and predecessor manifest are governed (1.738608ms)
✔ I09 C1 validate:i09 restores full I04 predecessor regression (0.844071ms)
✔ I09 C1 DB concurrency proof cannot pass through one coalesced store transaction (0.655817ms)
✔ I09 C1 real contention proof does not count manual RAISE as burst contention (3.880974ms)
✔ I09 C1 mixed-stage races are mandatory in validator evidence (0.734607ms)
ℹ tests 20
ℹ suites 0
ℹ pass 20
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 264.157555
   Compiling version_check v0.9.5
   Compiling typenum v1.20.1
   Compiling proc-macro2 v1.0.107
   Compiling unicode-ident v1.0.24
   Compiling quote v1.0.47
   Compiling generic-array v0.14.7
   Compiling autocfg v1.5.1
   Compiling semver v1.0.28
   Compiling rustc_version v0.4.1
   Compiling num-traits v0.2.19
   Compiling serde_core v1.0.229
   Compiling curve25519-dalek v4.1.3
   Compiling syn v2.0.119
   Compiling serde v1.0.229
   Compiling cpufeatures v0.2.17
   Compiling cfg-if v1.0.4
   Compiling crypto-common v0.1.7
   Compiling block-buffer v0.10.4
   Compiling digest v0.10.7
   Compiling signature v2.2.0
   Compiling serde_json v1.0.117
   Compiling subtle v2.6.1
   Compiling anyhow v1.0.86
   Compiling zeroize v1.9.0
   Compiling num-integer v0.1.47
   Compiling ed25519 v2.2.3
   Compiling sha2 v0.10.8
   Compiling ryu v1.0.23
   Compiling itoa v1.0.18
   Compiling num-bigint v0.4.6
   Compiling base64 v0.22.1
   Compiling curve25519-dalek-derive v0.1.1
   Compiling ed25519-dalek v2.1.1
   Compiling epd2-i08-verifier-c v0.1.0 (/tmp/pb01-i09-c2-diag-v2/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/verifier/rust)
    Finished `release` profile [optimized] target(s) in 7.13s

> epd2-pb01-i06-candidate@0.1.0 verify:i08:rust
> node scripts/i08_verify_rust.mjs positives

{"invokes_belenios":false,"invokes_go":false,"invokes_node":false,"mutation_count":"0","mutation_results":[],"mutations_rejected":"0","positive_vector_count":"4","producer_imports":false,"schema_version":"epd2.pb01.i08-rust-verifier-result/1","status":"PASS","toolchain_policy":"1.97.1","vector_results":[{"aggregate_digest":"5e295e8fd222a03b5c50d1b1bf7188620bf8db38f986f25c55a8793a2c094679","ceremony_digest":"349223d8a1a59fe480d6774df7c08912c0d2dd2df64f73ca7ec719ead0c35236","decryption_record_digest":"ab25b78657494d96c6e303242512bd8c316cc35793dfd9f838d513c33135baae","election_digest":"3a4b152f2f34b9f78318619b64c5d282d5d497ba9cb3a01618fadac6162d3d27","final_set_reference":"4d33ca52ac94a90c22049dc017e7a69a53dbbd7211308c54722383d6753605d1","plaintext_tally_digest":"580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c","public_evidence_bundle_digest":"d15194b1bb5c8ad10e8cf9402c9c8b1dcd0fc575597f583e5121c70b712fa0cc","public_result_digest":"550ed2b41b465f71b615ce3805cfb884a2f6d16f9780b8bad96694a5718b001e","share_digests":["e56f69730ed30a8530a78352d861f937a76d12cd8996d9c0f1641bd067da24f7","ef5fee15828ba66192a6f2480edd8ba83a61361fd3da8bd76b9f640ff0aa6d40"],"status":"PASS","vector_id":"I07-V01"},{"aggregate_digest":"5e295e8fd222a03b5c50d1b1bf7188620bf8db38f986f25c55a8793a2c094679","ceremony_digest":"349223d8a1a59fe480d6774df7c08912c0d2dd2df64f73ca7ec719ead0c35236","decryption_record_digest":"ab25b78657494d96c6e303242512bd8c316cc35793dfd9f838d513c33135baae","election_digest":"3a4b152f2f34b9f78318619b64c5d282d5d497ba9cb3a01618fadac6162d3d27","final_set_reference":"4d33ca52ac94a90c22049dc017e7a69a53dbbd7211308c54722383d6753605d1","plaintext_tally_digest":"580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c","public_evidence_bundle_digest":"1466f5c6479911da060f642d4fba08424703c7380d4aa2cb154be315d2d6f2da","public_result_digest":"550ed2b41b465f71b615ce3805cfb884a2f6d16f9780b8bad96694a5718b001e","share_digests":["e56f69730ed30a8530a78352d861f937a76d12cd8996d9c0f1641bd067da24f7","ef5fee15828ba66192a6f2480edd8ba83a61361fd3da8bd76b9f640ff0aa6d40","d19e010be386dd735c96a0ba444aabbea6d6d5865227c3e01f1dd26860b34d4b"],"status":"PASS","vector_id":"I07-V02"},{"aggregate_digest":"5e295e8fd222a03b5c50d1b1bf7188620bf8db38f986f25c55a8793a2c094679","ceremony_digest":"349223d8a1a59fe480d6774df7c08912c0d2dd2df64f73ca7ec719ead0c35236","decryption_record_digest":"ab25b78657494d96c6e303242512bd8c316cc35793dfd9f838d513c33135baae","election_digest":"3a4b152f2f34b9f78318619b64c5d282d5d497ba9cb3a01618fadac6162d3d27","final_set_reference":"4d33ca52ac94a90c22049dc017e7a69a53dbbd7211308c54722383d6753605d1","plaintext_tally_digest":"580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c","public_evidence_bundle_digest":"1466f5c6479911da060f642d4fba08424703c7380d4aa2cb154be315d2d6f2da","public_result_digest":"550ed2b41b465f71b615ce3805cfb884a2f6d16f9780b8bad96694a5718b001e","share_digests":["e56f69730ed30a8530a78352d861f937a76d12cd8996d9c0f1641bd067da24f7","ef5fee15828ba66192a6f2480edd8ba83a61361fd3da8bd76b9f640ff0aa6d40","d19e010be386dd735c96a0ba444aabbea6d6d5865227c3e01f1dd26860b34d4b"],"status":"PASS","vector_id":"I07-V03"},{"aggregate_digest":"7e6beffefc73c8103d2dab246bce4651a9bcc5330b081a533cadc6b792c45837","ceremony_digest":"56f267a4f7b97af768eb4b77ab108bf5b4a4ae7ffa351bd893c801363889d304","decryption_record_digest":"6cab8be2cf8f4db1024d1ba78168924b74f77f1008cc18b855b44b3c1c03e8ad","election_digest":"b99461b29f37a7ccc4c1022f88bd7add2fe61482fa7c3a276c4aaf5348367955","final_set_reference":"3de669d8adc92f417919af7d9ba9691945a83e5171844d34c15a49805d6243d6","plaintext_tally_digest":"34ed65c6fe5fe649af9223803d39b30259c000b9f5605503a39c7259ab7eedda","public_evidence_bundle_digest":"2f9ac3d8805b27941c35918f663dde7a17f12a49fe22a7f106319d991e871748","public_result_digest":"2b1de73c9d19a3bdaa9cd2248e440dd4ae40f7c50f9e01fbbb3db87fdb8f6978","share_digests":["5e4a20157d368cdbf66fea465e53886a01f6710aa0915e19f2cd38b4b82cccec","81d81fe34a500c186c2a68d2337fcb029c994951d46b74e30a7afae05a5435b1"],"status":"PASS","vector_id":"I07-V04"}],"verifier":"independent-rust-verifier-c"}

> epd2-pb01-i06-candidate@0.1.0 verify:i08:rust:negatives
> node scripts/i08_verify_rust.mjs negatives

{"invokes_belenios":false,"invokes_go":false,"invokes_node":false,"mutation_count":"26","mutation_results":[{"mutation_id":"I07-N01","reason":"I07_ELECTION_CROSS_BIND","status":"REJECT"},{"mutation_id":"I07-N02","reason":"I07_ELECTION_CROSS_BIND","status":"REJECT"},{"mutation_id":"I07-N03","reason":"I06_RECORD_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N04","reason":"I07_FINAL_SET_CROSS_BIND","status":"REJECT"},{"mutation_id":"I07-N05","reason":"I05_EVIDENCE_DIGEST","status":"REJECT"},{"mutation_id":"I07-N06","reason":"I05_EVIDENCE_DIGEST","status":"REJECT"},{"mutation_id":"I07-N07","reason":"I06_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N08","reason":"I06_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N09","reason":"I06_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N10","reason":"I06_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N11","reason":"I06_DUPLICATE_GUARDIAN","status":"REJECT"},{"mutation_id":"I07-N12","reason":"I08_SHARE_RAW_JSON","status":"REJECT"},{"mutation_id":"I07-N13","reason":"GROUP_POINT_INVALID","status":"REJECT"},{"mutation_id":"I07-N14","reason":"I08_PARTIAL_DECRYPTION_PROOF","status":"REJECT"},{"mutation_id":"I07-N15","reason":"I06_SHARE_DIGEST","status":"REJECT"},{"mutation_id":"I07-N16","reason":"I06_THRESHOLD_MEMBERSHIP","status":"REJECT"},{"mutation_id":"I07-N17","reason":"I06_RECORD","status":"REJECT"},{"mutation_id":"I07-N18","reason":"I06_RECORD","status":"REJECT"},{"mutation_id":"I07-N19","reason":"I06_RECORD","status":"REJECT"},{"mutation_id":"I07-N20","reason":"I06_RECORD","status":"REJECT"},{"mutation_id":"I07-N21","reason":"I07_RESULT_BIND","status":"REJECT"},{"mutation_id":"I07-N22","reason":"I07_ELECTION_CROSS_BIND","status":"REJECT"},{"mutation_id":"I07-N23","reason":"I07_RESULT_BIND","status":"REJECT"},{"mutation_id":"I07-N24","reason":"I06_RECORD_CEREMONY","status":"REJECT"},{"mutation_id":"I07-N25","reason":"FIELD_REQUIRED:i06_accepted_partial_decryption_shares","status":"REJECT"},{"mutation_id":"I07-N26","reason":"I07_SCHEMA","status":"REJECT"}],"mutations_rejected":"26","positive_vector_count":"0","producer_imports":false,"schema_version":"epd2.pb01.i08-rust-verifier-result/1","status":"PASS","toolchain_policy":"1.97.1","vector_results":[],"verifier":"independent-rust-verifier-c"}

> epd2-pb01-i06-candidate@0.1.0 verify:i08:agreement
> node scripts/i08_cross_language_agreement.mjs

{"schema_version":"epd2.pb01.i08-node-go-rust-agreement/1","run_nonce":"a162c769d8bdbe1506ffe90e1cd54046","verifier_a":"independent-node-verifier-a","verifier_b":"independent-go-verifier-b","verifier_c":"independent-rust-verifier-c","rust_executable":{"path":"/tmp/pb01-i09-c2-diag-v2/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/verifier/rust/target/release/epd2-i08-verifier-c","class":"fresh_build","sha256":"3b0aa75c4023e9140fae5c4c6e594607f91b08756ca8d833e0e81357cdc66b8e"},"live_recomputed":true,"vector_count":"4","vector_results":[{"vector_id":"I07-V01","byte_for_byte_agreement":true,"fields":["status","election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]},{"vector_id":"I07-V02","byte_for_byte_agreement":true,"fields":["status","election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]},{"vector_id":"I07-V03","byte_for_byte_agreement":true,"fields":["status","election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]},{"vector_id":"I07-V04","byte_for_byte_agreement":true,"fields":["status","election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]}],"byte_for_byte_agreement":true,"status":"PASS"}

> epd2-pb01-i06-candidate@0.1.0 test:i09:concurrency
> bash scripts/run_i09_c1_concurrency.sh

✔ I09 C1/PG 16 execute callers use 16 independent stores/DB transactions and converge (278.930906ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 378.68047
✔ I09 C1/PG 8 execute callers use 8 independent stores/DB transactions and converge (372.382418ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 467.087983
✔ I09 C1/PG 4 execute callers use 4 independent stores/DB transactions and converge (661.127746ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 752.403056
✔ I09 C1/PG 2 execute callers use 2 independent stores/DB transactions and converge (274.786937ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 369.739729
✔ I09/PG deterministic injected 40001 remains a retry-policy test only (268.765761ms)
✔ I09/PG retry budget exhausted produces explicit operational failure and no tally (238.456975ms)
✔ I09/PG non-retryable database SQLSTATE fails immediately (164.131067ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 762.648433
✔ I09 C1/PG burst produces 40001 from real concurrent SERIALIZABLE transactions and converges (659.016487ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 752.247087
✔ I09 C1 mixed A: tally during uncommitted finalization fails closed, retry after commit yields one canonical tally (347.339525ms)
✔ I09 C1 mixed B: publication cannot cross an uncommitted decryption boundary (1234.664871ms)
✔ I09 C1 mixed C: read-only verifier sees no bundle during publication transaction, then complete canonical bundle PASS (1008.700174ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2693.613634
{"status":"C1_CONCURRENCY_AND_MIXED_PASS","postgresql_version":"postgres (PostgreSQL) 16.14 (Ubuntu 16.14-1.pgdg24.04+1)"}

> epd2-pb01-i06-candidate@0.1.0 test:i09:crash
> bash scripts/run_i09_postgres_class.sh tests/i05-postgres-crash-restart.test.mjs tests/i06-postgres-concurrency-crash.test.mjs tests/i07-postgres-crash.test.mjs

✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (724.164969ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (893.804051ms)
✔ I06/PG concurrent final threshold shares converge to one immutable record (1026.642304ms)
✔ I06/PG same-guardian concurrent duplicate race never double-counts threshold (540.050527ms)
✔ I06/PG CRASH-01 retry deterministically converges (651.96132ms)
✔ I06/PG CRASH-02 retry deterministically converges (661.591ms)
✔ I06/PG CRASH-03 retry deterministically converges (644.973377ms)
✔ I06/PG CRASH-04 retry deterministically converges (714.325522ms)
✔ I07/PG crash before_result_persistence leaves no incomplete FINAL and retry converges (1223.483076ms)
✔ I07/PG crash after_result_persistence_before_evidence_publication_marker leaves no incomplete FINAL and retry converges (903.75126ms)
✔ I07/PG crash after_evidence_persistence_before_final_status_transition leaves no incomplete FINAL and retry converges (886.665459ms)
✔ I07/PG crash immediately after FINAL commit before response preserves one final result and retry is idempotent (885.092161ms)
ℹ tests 12
ℹ suites 0
ℹ pass 12
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 10030.435368

> epd2-pb01-i06-candidate@0.1.0 test:i09:restart
> bash scripts/run_i09_postgres_class.sh tests/i05-postgres-crash-restart.test.mjs tests/i06-postgres-restart-backup.test.mjs tests/i07-postgres-restart-backup.test.mjs

✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (666.529804ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (1543.024939ms)
✔ I06/PG hard database crash/restart preserves same immutable plaintext and record digest (1260.477452ms)
✔ I06/PG backup/restore preserves exact public ceremony/share/decryption evidence and no private guardian columns exist (811.875962ms)
✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (1689.736384ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1350.411808ms)
ℹ tests 6
ℹ suites 0
ℹ pass 6
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 7588.970722

> epd2-pb01-i06-candidate@0.1.0 test:i09:backup-restore
> bash scripts/run_i09_postgres_class.sh tests/i07-postgres-restart-backup.test.mjs

✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (1818.563788ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1440.238453ms)
ℹ tests 2
ℹ suites 0
ℹ pass 2
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3361.428041

> epd2-pb01-i06-candidate@0.1.0 test:i09:postgres
> I09_PG_STAGE=i03 bash scripts/run_i09_postgres_class.sh tests/postgres.integration.test.mjs tests/postgres-crash-concurrency.test.mjs tests/postgres-tamper-backup-roles.test.mjs && I09_PG_STAGE=i04 bash scripts/run_i09_postgres_class.sh tests/i04-finalization.integration.test.mjs tests/i04-concurrency-crash.test.mjs tests/i04-tamper-backup-roles.test.mjs && I09_PG_STAGE=i05 bash scripts/run_i09_postgres_class.sh tests/i05-postgres.integration.test.mjs tests/i05-postgres-runtime.test.mjs tests/i05-postgres-crash-restart.test.mjs tests/i05-postgres-tamper-backup-roles.test.mjs && I09_PG_STAGE=i06 bash scripts/run_i09_postgres_class.sh tests/i06-postgres-ceremony-decryption.test.mjs tests/i06-postgres-concurrency-crash.test.mjs tests/i06-postgres-restart-backup.test.mjs tests/i06-postgres-tamper-roles.test.mjs && I09_PG_STAGE=i07 bash scripts/run_i09_postgres_class.sh tests/i07-postgres-publication.test.mjs tests/i07-postgres-crash.test.mjs tests/i07-postgres-tamper.test.mjs tests/i07-postgres-restart-backup.test.mjs

✔ PG concurrent same key and same digest create one logical acceptance (140.670813ms)
✔ PG concurrent legitimate revotes coexist under one private lifecycle (81.556559ms)
✔ PG CRASH-01 after crypto before transaction leaves no accepted state (52.145819ms)
✔ PG CRASH-02/04 committed response loss survives service restart and retry (78.98285ms)
✔ PG CRASH-03 client disconnect cannot lose a committed acceptance (77.994508ms)
✔ PG append-only triggers and hash-chain checkpoint detect privileged tampering (152.194749ms)
✔ PG backup/restore preserves exact bytes, receipt state, ledger and private/public split (197.380411ms)
✔ PG submission runtime and evidence reader have no DDL or mutation authority (54.24963ms)
✔ PG-I03-P01 real I02 ballot follows native verification and PostgreSQL acceptance (178.447022ms)
✔ PG-I03-P02 idempotent retry returns same receipt; same key with different ballot conflicts (109.464003ms)
ℹ tests 10
ℹ suites 0
ℹ pass 10
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1363.596561
✔ I04 concurrent identical and conflicting finalizers converge without split state (181.105873ms)
✔ I04-CRASH-01 is atomic and retry converges (113.360528ms)
✔ I04-CRASH-02 is atomic and retry converges (106.22649ms)
✔ I04-CRASH-03 is atomic and retry converges (104.408544ms)
✔ I04-CRASH-04 is atomic and retry converges (102.880573ms)
✔ I04 submission-versus-closure race has one deterministic boundary outcome (127.375214ms)
✔ I04 real I03 revote E2E selects latest valid, preserves history and exact bytes (196.186955ms)
✔ I04 multi-lifecycle resolution yields A2, B1 and C3 in I01 digest order (208.007127ms)
✔ I04 empty election finalizes deterministically (81.220169ms)
✔ I04 public verifier detects every committed-field tamper class (190.641922ms)
✔ I04 refuses finalization when I03 ledger integrity has been altered (99.315887ms)
✔ I04 PostgreSQL roles enforce submission/finalizer/evidence/migration separation (250.408541ms)
✔ I04 backup/restore preserves exact I03 history and identical final artifacts (610.752083ms)
ℹ tests 13
ℹ suites 0
ℹ pass 13
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2624.099708
✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (682.079036ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (636.074809ms)
✔ I05/PG exact finalized I04 set becomes the tally input and native Belenios re-verification runs per ballot (226.411674ms)
✔ I05/PG idempotent retry replays one physical tally without recomputing a second record (220.404885ms)
✔ I05/PG concurrent tally executions never diverge and every caller converges on one identical tally (154.66927ms)
✔ I05/PG rejects a conflicting F_final and a conflicting tally record against the same election (193.988132ms)
✔ I05/PG recompute reproduces the committed tally byte-for-byte from PostgreSQL state (300.625482ms)
✔ I05/PG append-only triggers reject mutation of committed tally state even for the schema owner (221.627856ms)
✔ I05/PG privileged tamper that bypasses the triggers is still detected by evidence and recompute (227.033384ms)
✔ I05/PG tally runtime cannot mutate I03 or I04 state (162.548422ms)
✔ I05/PG submission, finalizer and evidence roles cannot mutate I05 tally state (197.251054ms)
✔ I05/PG tally and evidence roles hold no DDL or TEMP privilege anywhere (159.956786ms)
✔ I05/PG backup and restore preserve exact aggregate and tally bytes and every digest (459.176516ms)
✔ I05 PostgreSQL exact finalized set tally, idempotency, recompute, concurrency and privileges (286.933528ms)
✔ I05 PostgreSQL CRASH-03 rolls aggregate insert back; retry converges (188.439624ms)
ℹ tests 15
ℹ suites 0
ℹ pass 15
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 4664.890361
✔ I06/PG real threshold ceremony freezes immutable N=3 T=2 public context (496.632585ms)
✔ I06/PG T-1 exposes no plaintext; exact threshold commits one immutable result; extra valid share cannot change plaintext (701.31025ms)
✔ I06/PG duplicate guardian and malformed/invalid share fail closed (413.547448ms)
✔ I06/PG concurrent final threshold shares converge to one immutable record (825.206027ms)
✔ I06/PG same-guardian concurrent duplicate race never double-counts threshold (272.788522ms)
✔ I06/PG CRASH-01 retry deterministically converges (699.628984ms)
✔ I06/PG CRASH-02 retry deterministically converges (502.572068ms)
✔ I06/PG CRASH-03 retry deterministically converges (662.479958ms)
✔ I06/PG CRASH-04 retry deterministically converges (528.163891ms)
✔ I06/PG hard database crash/restart preserves same immutable plaintext and record digest (1323.495241ms)
✔ I06/PG backup/restore preserves exact public ceremony/share/decryption evidence and no private guardian columns exist (786.965717ms)
✔ I06/PG mandatory I05 corrective detects privileged aggregate-byte-only rewrite and decryption refuses (812.008546ms)
✔ I06/PG privileged tamper: guardian public key after freeze is detected (408.264665ms)
✔ I06/PG privileged tamper: threshold after ceremony freeze is detected (421.190956ms)
✔ I06/PG privileged tamper: frozen guardian-set member replacement is detected (417.274828ms)
✔ I06/PG privileged tamper: partial-decryption factor bytes are detected (438.549725ms)
✔ I06/PG privileged tamper: partial-decryption proof bytes are detected (422.901069ms)
✔ I06/PG privileged tamper: accepted share digest column is detected (411.034744ms)
✔ I06/PG privileged tamper: aggregate digest alone is detected (409.186132ms)
✔ I06/PG privileged tamper: final plaintext bytes are detected (640.552268ms)
✔ I06/PG privileged tamper: final decryption-record digest is detected (599.631266ms)
✔ I06/PG roles enforce coordinator/ingester/finalizer/runtime separation (412.549944ms)
ℹ tests 22
ℹ suites 0
ℹ pass 22
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 12978.036424
✔ I07/PG crash before_result_persistence leaves no incomplete FINAL and retry converges (1237.21842ms)
✔ I07/PG crash after_result_persistence_before_evidence_publication_marker leaves no incomplete FINAL and retry converges (888.224868ms)
✔ I07/PG crash after_evidence_persistence_before_final_status_transition leaves no incomplete FINAL and retry converges (869.738791ms)
✔ I07/PG crash immediately after FINAL commit before response preserves one final result and retry is idempotent (877.838681ms)
✔ I07/PG real persistence path publishes one final bundle independently verified by A and B (1423.847485ms)
✔ I07/PG concurrent publishers converge to one immutable canonical result (770.965978ms)
✔ I07/PG idempotent retry returns same result and conflicting direct commit is rejected (732.930691ms)
✔ I07/PG least privilege: publisher has only scoped I07 write + I06 authority read; public verifier is read-only FINAL view (580.835169ms)
✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (1886.161414ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1285.222177ms)
✔ I07/PG privileged tamper aggregate bytes is detected independently of DB permissions (877.4072ms)
✔ I07/PG privileged tamper guardian public key is detected independently of DB permissions (602.924978ms)
✔ I07/PG privileged tamper threshold is detected independently of DB permissions (603.879693ms)
✔ I07/PG privileged tamper accepted share artifact is detected independently of DB permissions (601.32675ms)
✔ I07/PG privileged tamper accepted share digest is detected independently of DB permissions (607.538474ms)
✔ I07/PG privileged tamper plaintext bytes is detected independently of DB permissions (613.000495ms)
✔ I07/PG privileged tamper plaintext digest is detected independently of DB permissions (609.013595ms)
✔ I07/PG privileged tamper decryption record canonical is detected independently of DB permissions (632.412857ms)
✔ I07/PG privileged tamper public result canonical bytes is detected independently of DB permissions (726.558429ms)
✔ I07/PG privileged tamper public result digest column is detected independently of DB permissions (721.196417ms)
ℹ tests 20
ℹ suites 0
ℹ pass 20
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 17523.398122
{"status":"PASS","postgresql_version":"postgres (PostgreSQL) 16.14 (Ubuntu 16.14-1.pgdg24.04+1)"}

> epd2-pb01-i06-candidate@0.1.0 test:i09:scale
> node scripts/i09_scale_worker.mjs 100 && node scripts/i09_scale_worker.mjs 1000 && node scripts/i09_scale_worker.mjs 10000

I09_SCALE_PROGRESS:I09-S100:setup
I09_SCALE_PROGRESS:I09-S100:ballots:947
I09_SCALE_PROGRESS:I09-S100:finalset:11
I09_SCALE_PROGRESS:I09-S100:tally:293
I09_SCALE_PROGRESS:I09-S100:decrypt:566
I09_SCALE_PROGRESS:I09-S100:evidence:7
{"schema_version":"epd2.pb01.i09-scale-result/1","fixture_id":"I09-S100","raw_submissions":110,"effective_final_set_size":100,"revote_count":10,"timings_ms":{"setup_and_credentials":160,"ballot_validation_and_generation":947,"final_set_derivation":11,"tally_computation":293,"decryption_verification":566,"result_evidence_generation":7,"independent_rust_verification":10},"result_digest":"5973a8c96035f11f14b45fff34738bc137ebbfc17b20a22d085d2b767d271d1c","aggregate_digest":"3a3831a1079f0819ade3e5d9be3a0e68f67295fa70ea3c5dd4bea70534b4be26","plaintext_tally":[["33","34","33"]],"verifier_result":{"node":"PASS","go":"PASS","rust":"PASS","byte_for_byte_agreement":true},"resource_observations":{"peak_memory":"measured externally where runner supports /usr/bin/time; no SLA claim"},"status":"PASS"}
I09_SCALE_PROGRESS:I09-S1000:setup
I09_SCALE_PROGRESS:I09-S1000:ballots:9220
I09_SCALE_PROGRESS:I09-S1000:finalset:34
I09_SCALE_PROGRESS:I09-S1000:tally:1292
I09_SCALE_PROGRESS:I09-S1000:decrypt:5072
I09_SCALE_PROGRESS:I09-S1000:evidence:40
{"schema_version":"epd2.pb01.i09-scale-result/1","fixture_id":"I09-S1000","raw_submissions":1100,"effective_final_set_size":1000,"revote_count":100,"timings_ms":{"setup_and_credentials":359,"ballot_validation_and_generation":9220,"final_set_derivation":34,"tally_computation":1292,"decryption_verification":5072,"result_evidence_generation":40,"independent_rust_verification":36},"result_digest":"d245d2efeacb398df6d67d50e8727c508ca08699011e09822527567319190e33","aggregate_digest":"e650191fcad1b31782ead02807387efb6789764d44c76651e209e73631772995","plaintext_tally":[["333","334","333"]],"verifier_result":{"node":"PASS","go":"PASS","rust":"PASS","byte_for_byte_agreement":true},"resource_observations":{"peak_memory":"measured externally where runner supports /usr/bin/time; no SLA claim"},"status":"PASS"}
I09_SCALE_PROGRESS:I09-S10000:setup
I09_SCALE_PROGRESS:I09-S10000:ballots:91681
I09_SCALE_PROGRESS:I09-S10000:finalset:271
I09_SCALE_PROGRESS:I09-S10000:tally:11285
I09_SCALE_PROGRESS:I09-S10000:decrypt:50231
I09_SCALE_PROGRESS:I09-S10000:evidence:302
{"schema_version":"epd2.pb01.i09-scale-result/1","fixture_id":"I09-S10000","raw_submissions":11000,"effective_final_set_size":10000,"revote_count":1000,"timings_ms":{"setup_and_credentials":2236,"ballot_validation_and_generation":91681,"final_set_derivation":271,"tally_computation":11285,"decryption_verification":50231,"result_evidence_generation":302,"independent_rust_verification":265},"result_digest":"b6750e454366d2aafd19836279c8bc16f01ec84692be02a45dafb06eec7d5d8b","aggregate_digest":"9993ab45232e3c7becc6d6da199c60d73874a410a01099145509d2b286ad4f36","plaintext_tally":[["3333","3334","3333"]],"verifier_result":{"node":"PASS","go":"PASS","rust":"PASS","byte_for_byte_agreement":true},"resource_observations":{"peak_memory":"measured externally where runner supports /usr/bin/time; no SLA claim"},"status":"PASS"}

> epd2-pb01-i06-candidate@0.1.0 verify:i09:agreement
> node scripts/i09_verify_agreement.mjs

{"schema_version":"epd2.pb01.i09-scale-agreement/1","results":[{"fixture_id":"I09-S1000","byte_for_byte_agreement":true,"fields":["election_digest","final_set_reference","aggregate_digest","ceremony_digest","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]},{"fixture_id":"I09-S10000","byte_for_byte_agreement":true,"fields":["election_digest","final_set_reference","aggregate_digest","ceremony_digest","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest"]}],"status":"PASS"}
{"schema_version":"epd2.pb01.i09-acceptance-harness/1","test_count":15,"pass_count":13,"results":[{"name":"missing PostgreSQL -> FAIL","status":"PASS"},{"name":"PostgreSQL !=16 -> FAIL","status":"PASS"},{"name":"wrong Node -> FAIL","status":"PASS"},{"name":"missing Rust -> FAIL","status":"PASS"},{"name":"changed Cargo.lock -> FAIL","status":"PASS"},{"name":"stale I09 result -> FAIL","status":"FAIL"},{"name":"retry disabled -> FAIL","status":"PASS"},{"name":"unbounded retry -> FAIL","status":"PASS"},{"name":"40001 divergence prevented","status":"PASS"},{"name":"10k test required","status":"PASS"},{"name":"fresh Rust required","status":"PASS"},{"name":"predecessor regression failure -> FAIL","status":"PASS"},{"name":"tampered result -> FAIL","status":"FAIL"},{"name":"packaged Rust cannot authorize","status":"PASS"},{"name":"NON_BINDING_PILOT preserved","status":"PASS"}],"status":"FAIL"}
file:///tmp/pb01-i09-c2-diag-v2/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/scripts/i09_validate_current_run.mjs:28
      : rejectRun(Object.assign(new Error(`${cmd} ${args.join(' ')} exit ${code}: ${Buffer.concat(err).toString().slice(-4000)}`), { exitCode: code })));
                                ^

Error: /opt/hostedtoolcache/node/24.19.0/x64/bin/node scripts/i09_acceptance_harness.mjs exit 1: 
    at ChildProcess.<anonymous> (file:///tmp/pb01-i09-c2-diag-v2/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/scripts/i09_validate_current_run.mjs:28:33)
    at ChildProcess.emit (node:events:509:28)
    at ChildProcess._handle.onexit (node:internal/child_process:295:12) {
  exitCode: 1
}

Node.js v24.19.0
```
