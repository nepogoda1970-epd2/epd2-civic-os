# PB01-I06 External PostgreSQL Verification Result

**Verdict:** PASS — PB01-I06 external PostgreSQL gate passed

- Workflow run: 32178860189
- Commit: cabd32d186d51a2fc947153c91e9071d0fc46f2d
- Candidate: `EPD2_VCRYPTO-PB01-I06_GUARDIAN_CEREMONY_AND_THRESHOLD_DECRYPTION_CANDIDATE_0.2_C1.zip`
- Expected SHA-256: `25114f10c95664e5145e4efc7c381aba4a2d9c3edc83760ee5e9bc72e55c532e`
- Integrity rc: 0
- Dependency install rc: 0
- Crypto/verifier rc: 0
- PostgreSQL 16 rc: 0

## Integrity log (tail)
```text
./test-vectors/i06/fixtures/n3-t2-empty/trustees.public.json: OK
./test-vectors/i06/fixtures/n3-t2/UUID.txt: OK
./test-vectors/i06/fixtures/n3-t2/decryption-base.bel: OK
./test-vectors/i06/fixtures/n3-t2/election.public.json: OK
./test-vectors/i06/fixtures/n3-t2/encrypted_tally.out: OK
./test-vectors/i06/fixtures/n3-t2/public-metadata.json: OK
./test-vectors/i06/fixtures/n3-t2/public_creds.json: OK
./test-vectors/i06/fixtures/n3-t2/result-all.json: OK
./test-vectors/i06/fixtures/n3-t2/result-alt-threshold.json: OK
./test-vectors/i06/fixtures/n3-t2/result-threshold.json: OK
./test-vectors/i06/fixtures/n3-t2/setup-base.bel: OK
./test-vectors/i06/fixtures/n3-t2/share-1.json: OK
./test-vectors/i06/fixtures/n3-t2/share-2.json: OK
./test-vectors/i06/fixtures/n3-t2/share-3.json: OK
./test-vectors/i06/fixtures/n3-t2/threshold.json: OK
./test-vectors/i06/fixtures/n3-t2/trustees.public.json: OK
./test-vectors/i06/fixtures/n5-t3/UUID.txt: OK
./test-vectors/i06/fixtures/n5-t3/decryption-base.bel: OK
./test-vectors/i06/fixtures/n5-t3/election.public.json: OK
./test-vectors/i06/fixtures/n5-t3/encrypted_tally.out: OK
./test-vectors/i06/fixtures/n5-t3/public-metadata.json: OK
./test-vectors/i06/fixtures/n5-t3/public_creds.json: OK
./test-vectors/i06/fixtures/n5-t3/result-all.json: OK
./test-vectors/i06/fixtures/n5-t3/result-alt-threshold.json: OK
./test-vectors/i06/fixtures/n5-t3/result-threshold.json: OK
./test-vectors/i06/fixtures/n5-t3/setup-base.bel: OK
./test-vectors/i06/fixtures/n5-t3/share-1.json: OK
./test-vectors/i06/fixtures/n5-t3/share-2.json: OK
./test-vectors/i06/fixtures/n5-t3/share-3.json: OK
./test-vectors/i06/fixtures/n5-t3/share-4.json: OK
./test-vectors/i06/fixtures/n5-t3/share-5.json: OK
./test-vectors/i06/fixtures/n5-t3/threshold.json: OK
./test-vectors/i06/fixtures/n5-t3/trustees.public.json: OK
./test-vectors/i06/index.json: OK
./test-vectors/i06/mutations/I06-N01.json: OK
./test-vectors/i06/mutations/I06-N02.json: OK
./test-vectors/i06/mutations/I06-N03.json: OK
./test-vectors/i06/mutations/I06-N04.json: OK
./test-vectors/i06/mutations/I06-N05.json: OK
./test-vectors/i06/mutations/I06-N06.json: OK
./test-vectors/i06/mutations/I06-N07.json: OK
./test-vectors/i06/mutations/I06-N08.json: OK
./test-vectors/i06/mutations/I06-N09.json: OK
./test-vectors/i06/mutations/index.json: OK
./test-vectors/i06/vectors/I06-V01.json: OK
./test-vectors/i06/vectors/I06-V02.json: OK
./test-vectors/i06/vectors/I06-V03.json: OK
./test-vectors/i06/vectors/I06-V04.json: OK
./test-vectors/negative/I03-negative-vectors.json: OK
./test-vectors/positive/I03-positive-vectors.json: OK
./test-vectors/real-i02/browser-produced-submission.json: OK
./tests/api.integration.test.mjs: OK
./tests/browser-to-ledger.e2e.mjs: OK
./tests/concurrency-crash.test.mjs: OK
./tests/helpers.mjs: OK
./tests/i04-browser-vector.e2e.mjs: OK
./tests/i04-concurrency-crash.test.mjs: OK
./tests/i04-cross-language-verifier.test.mjs: OK
./tests/i04-finalization.integration.test.mjs: OK
./tests/i04-performance.mjs: OK
./tests/i04-policy.unit.test.mjs: OK
./tests/i04-tamper-backup-roles.test.mjs: OK
./tests/i04_postgres_helpers.mjs: OK
./tests/i05-api-boundary.test.mjs: OK
./tests/i05-crash-concurrency.test.mjs: OK
./tests/i05-postgres-crash-restart.test.mjs: OK
./tests/i05-postgres-runtime.test.mjs: OK
./tests/i05-postgres-tamper-backup-roles.test.mjs: OK
./tests/i05-postgres.integration.test.mjs: OK
./tests/i05-static-security.test.mjs: OK
./tests/i05-vectors.test.mjs: OK
./tests/i05_postgres_helpers.mjs: OK
./tests/i06-api-boundary.test.mjs: OK
./tests/i06-i05-corrective.test.mjs: OK
./tests/i06-mutation-vectors.test.mjs: OK
./tests/i06-postgres-ceremony-decryption.test.mjs: OK
./tests/i06-postgres-concurrency-crash.test.mjs: OK
./tests/i06-postgres-restart-backup.test.mjs: OK
./tests/i06-postgres-tamper-roles.test.mjs: OK
./tests/i06-static-security.test.mjs: OK
./tests/i06-threshold-negatives.test.mjs: OK
./tests/i06-vectors.test.mjs: OK
./tests/i06_postgres_helpers.mjs: OK
./tests/ledger-tamper.test.mjs: OK
./tests/performance.mjs: OK
./tests/postgres-crash-concurrency.test.mjs: OK
./tests/postgres-tamper-backup-roles.test.mjs: OK
./tests/postgres.integration.test.mjs: OK
./tests/postgres_helpers.mjs: OK
./tests/security.test.mjs: OK
./tests/unit.test.mjs: OK
./vendor/npm/axe-core-4.10.3.tgz: OK
./vendor/npm/fsevents-2.3.2.tgz: OK
./vendor/npm/pg-8.16.3.tgz: OK
./vendor/npm/pg-cloudflare-1.4.0.tgz: OK
./vendor/npm/pg-connection-string-2.14.0.tgz: OK
./vendor/npm/pg-int8-1.0.1.tgz: OK
./vendor/npm/pg-pool-3.14.0.tgz: OK
./vendor/npm/pg-protocol-1.16.0.tgz: OK
./vendor/npm/pg-types-2.2.0.tgz: OK
./vendor/npm/pgpass-1.0.5.tgz: OK
./vendor/npm/playwright-1.62.1.tgz: OK
./vendor/npm/playwright-core-1.62.1.tgz: OK
./vendor/npm/postgres-array-2.0.0.tgz: OK
./vendor/npm/postgres-bytea-1.0.1.tgz: OK
./vendor/npm/postgres-date-1.0.7.tgz: OK
./vendor/npm/postgres-interval-1.2.0.tgz: OK
./vendor/npm/split2-4.2.0.tgz: OK
./vendor/npm/xtend-4.0.2.tgz: OK
./verifier/i04_verifier_b.mjs: OK
./verifier/i05_verifier_a.mjs: OK
./verifier/i06_verifier_a.mjs: OK
./verifier/reference-go-i05/main.go: OK
./verifier/reference-go-i06/main.go: OK
./verifier/reference-go/go.mod: OK
./verifier/reference-go/main.go: OK
./verifier/rust/Cargo.toml: OK
./verifier/rust/README.md: OK
./verifier/rust/src/main.rs: OK
./verifier/verify-i04-evidence.mjs: OK
```

## Dependency log (tail)
```text
npm warn EBADENGINE Unsupported engine {
npm warn EBADENGINE   package: 'epd2-pb01-i06-candidate@0.1.0',
npm warn EBADENGINE   required: { node: '24.19.0' },
npm warn EBADENGINE   current: { node: 'v22.23.2', npm: '10.9.8' }
npm warn EBADENGINE }

added 17 packages, and audited 18 packages in 909ms

found 0 vulnerabilities
```

## Crypto / verifier log (tail)
```text
# (node:2842) ExperimentalWarning: SQLite is an experimental feature and might change at any time
# (Use `node --trace-warnings ...` to show where the warning was created)
# Subtest: I06-N01 frozen mutation vector rejects
ok 4 - I06-N01 frozen mutation vector rejects
  ---
  duration_ms: 6.940643
  type: 'test'
  ...
# Subtest: I06-N02 frozen mutation vector rejects
ok 5 - I06-N02 frozen mutation vector rejects
  ---
  duration_ms: 2.662344
  type: 'test'
  ...
# Subtest: I06-N03 frozen mutation vector rejects
ok 6 - I06-N03 frozen mutation vector rejects
  ---
  duration_ms: 1.375645
  type: 'test'
  ...
# Subtest: I06-N04 frozen mutation vector rejects
ok 7 - I06-N04 frozen mutation vector rejects
  ---
  duration_ms: 46.442117
  type: 'test'
  ...
# Subtest: I06-N05 frozen mutation vector rejects
ok 8 - I06-N05 frozen mutation vector rejects
  ---
  duration_ms: 46.888222
  type: 'test'
  ...
# Subtest: I06-N06 frozen mutation vector rejects
ok 9 - I06-N06 frozen mutation vector rejects
  ---
  duration_ms: 39.559015
  type: 'test'
  ...
# Subtest: I06-N07 frozen mutation vector rejects
ok 10 - I06-N07 frozen mutation vector rejects
  ---
  duration_ms: 1.21181
  type: 'test'
  ...
# Subtest: I06-N08 frozen mutation vector rejects
ok 11 - I06-N08 frozen mutation vector rejects
  ---
  duration_ms: 0.952195
  type: 'test'
  ...
# Subtest: I06-N09 frozen mutation vector rejects
ok 12 - I06-N09 frozen mutation vector rejects
  ---
  duration_ms: 1.142079
  type: 'test'
  ...
# (node:2878) ExperimentalWarning: SQLite is an experimental feature and might change at any time
# (Use `node --trace-warnings ...` to show where the warning was created)
# Subtest: candidate contains no guardian private key material or decryption/admin secret API
ok 13 - candidate contains no guardian private key material or decryption/admin secret API
  ---
  duration_ms: 32.62367
  type: 'test'
  ...
# Subtest: I06 source has no plaintext result before threshold API route and no arbitrary aggregate input surface
ok 14 - I06 source has no plaintext result before threshold API route and no arbitrary aggregate input surface
  ---
  duration_ms: 1.898781
  type: 'test'
  ...
# (node:2890) ExperimentalWarning: SQLite is an experimental feature and might change at any time
# (Use `node --trace-warnings ...` to show where the warning was created)
# Subtest: mutation negatives: wrong aggregate/election/guardian/digests/plaintext/record fail closed
ok 15 - mutation negatives: wrong aggregate/election/guardian/digests/plaintext/record fail closed
  ---
  duration_ms: 3.674272
  type: 'test'
  ...
# Subtest: T-1 share has no Belenios plaintext result
ok 16 - T-1 share has no Belenios plaintext result
  ---
  duration_ms: 38.018255
  type: 'test'
  ...
# Subtest: invalid proof among threshold shares is rejected by pinned upstream Belenios
ok 17 - invalid proof among threshold shares is rejected by pinned upstream Belenios
  ---
  duration_ms: 48.105341
  type: 'test'
  ...
# Subtest: duplicate guardian cannot form threshold
ok 18 - duplicate guardian cannot form threshold
  ---
  duration_ms: 41.845686
  type: 'test'
  ...
# (node:2922) ExperimentalWarning: SQLite is an experimental feature and might change at any time
# (Use `node --trace-warnings ...` to show where the warning was created)
# Subtest: I06-V01 real Belenios threshold vector verifies
ok 19 - I06-V01 real Belenios threshold vector verifies
  ---
  duration_ms: 151.670405
  type: 'test'
  ...
# Subtest: I06-V02 real Belenios threshold vector verifies
ok 20 - I06-V02 real Belenios threshold vector verifies
  ---
  duration_ms: 195.234951
  type: 'test'
  ...
# Subtest: I06-V03 real Belenios threshold vector verifies
ok 21 - I06-V03 real Belenios threshold vector verifies
  ---
  duration_ms: 190.631227
  type: 'test'
  ...
# Subtest: I06-V04 real Belenios threshold vector verifies
ok 22 - I06-V04 real Belenios threshold vector verifies
  ---
  duration_ms: 120.139993
  type: 'test'
  ...
# Subtest: N=5 T=3 different valid threshold subsets and all five give identical plaintext
ok 23 - N=5 T=3 different valid threshold subsets and all five give identical plaintext
  ---
  duration_ms: 245.907192
  type: 'test'
  ...
1..23
# tests 23
# suites 0
# pass 23
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 2060.878048

> epd2-pb01-i06-candidate@0.1.0 verify:i06:a
> node verifier/i06_verifier_a.mjs

{"schema_version":"epd2.pb01.i06-verifier-a-result/1","verifier":"independent-node-reference-a","producer_imports":false,"vector_count":4,"vector_results":[{"vector_id":"I06-V01","status":"PASS","ceremony_digest":"349223d8a1a59fe480d6774df7c08912c0d2dd2df64f73ca7ec719ead0c35236","aggregate_digest":"5e295e8fd222a03b5c50d1b1bf7188620bf8db38f986f25c55a8793a2c094679","share_digests":["924cde8493e302b19c66d3e466d81e737eb5bfb5573c4e433701e1cea9a866f3","844d72cdb101b88b1916ea27b597cfd45caf815acd0d369d625e56b1787557c6","d800b786f43a8b2c2cc51451ec7dc67e04b935872b627ca5fdc15860156cbc6f"],"plaintext_tally_digest":"580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c","decryption_record_digest":"dae4fe38b011bb1d6604302f343eaa3af1752029e4a9887b8473537c4d882b55"},{"vector_id":"I06-V02","status":"PASS","ceremony_digest":"3fb99071a2d58a5b0aa9c111dc702d68726ba7382222552359dadbc544122488","aggregate_digest":"939b38407ac51adb91dba89dc215c97a526b5c0950a1cc6d19d7f8edf3cc2437","share_digests":["1368ba64d215cb29eeb9b3422f85e152be6d294e0aadaf7072ec7a309928c707","03f43be1e984df644a89d4010d5e5063b50bdb824be7670075f35e1ec83d5981","dd82759355846d827b841e456bdeebcca94b9c64a738f191c0712480d3a5cf78","6ec1f9f8957331ce2854e2458ffa7c22bea6e5f0cfbfac990df664374ff56228","4fbd340cdd6fc5e952772d38c81f9823370e613dd0fa4c4e3623372329a74e61"],"plaintext_tally_digest":"580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c","decryption_record_digest":"ecfd9da7f3d9d719f72f5c26a0dfadac67672f4169abef6329a49a542997b0ef"},{"vector_id":"I06-V03","status":"PASS","ceremony_digest":"3fb99071a2d58a5b0aa9c111dc702d68726ba7382222552359dadbc544122488","aggregate_digest":"939b38407ac51adb91dba89dc215c97a526b5c0950a1cc6d19d7f8edf3cc2437","share_digests":["1368ba64d215cb29eeb9b3422f85e152be6d294e0aadaf7072ec7a309928c707","03f43be1e984df644a89d4010d5e5063b50bdb824be7670075f35e1ec83d5981","dd82759355846d827b841e456bdeebcca94b9c64a738f191c0712480d3a5cf78","6ec1f9f8957331ce2854e2458ffa7c22bea6e5f0cfbfac990df664374ff56228","4fbd340cdd6fc5e952772d38c81f9823370e613dd0fa4c4e3623372329a74e61"],"plaintext_tally_digest":"580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c","decryption_record_digest":"ecfd9da7f3d9d719f72f5c26a0dfadac67672f4169abef6329a49a542997b0ef"},{"vector_id":"I06-V04","status":"PASS","ceremony_digest":"56f267a4f7b97af768eb4b77ab108bf5b4a4ae7ffa351bd893c801363889d304","aggregate_digest":"7e6beffefc73c8103d2dab246bce4651a9bcc5330b081a533cadc6b792c45837","share_digests":["73db7641fc3480b46ee96f2349940de36636469e4337083bf55d6ac99752b8a0","ce32e3e19d789b0f223362bf89e4e436dbbd711a3952103a52efb95d8fcd8c05","48e87b31369825242c875ee76392b0cee06fe71493c54471904f5c0c02f1e2f7"],"plaintext_tally_digest":"34ed65c6fe5fe649af9223803d39b30259c000b9f5605503a39c7259ab7eedda","decryption_record_digest":"7b9f3a94f276b8cd2eca2c896033b79b4437d473ea8d69bef37e01478be3d541"}],"mutation_negatives_rejected":6,"status":"PASS"}

> epd2-pb01-i06-candidate@0.1.0 verify:i06:b
> go run verifier/reference-go-i06/main.go --root . --tool evidence/build/belenios-tool-3.3.0-linux-x86_64 --out evidence/results/i06/cross-language-verifier.json

{
  "agreement_fields": [
    "ceremony digest",
    "aggregate reference digest",
    "share digests",
    "plaintext tally digest",
    "final decryption record digest"
  ],
  "byte_for_byte_agreement": true,
  "go_runtime_required": "1.23+",
  "producer_code_shared": false,
  "schema_version": "epd2.pb01.i06-verifier-b-result/1",
  "status": "PASS",
  "vector_count_decimal": "4",
  "vector_results": [
    {
      "aggregate_reference_digest": "5e295e8fd222a03b5c50d1b1bf7188620bf8db38f986f25c55a8793a2c094679",
      "ceremony_digest": "349223d8a1a59fe480d6774df7c08912c0d2dd2df64f73ca7ec719ead0c35236",
      "decryption_record_digest": "dae4fe38b011bb1d6604302f343eaa3af1752029e4a9887b8473537c4d882b55",
      "plaintext_tally_digest": "580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c",
      "share_digests": [
        "924cde8493e302b19c66d3e466d81e737eb5bfb5573c4e433701e1cea9a866f3",
        "844d72cdb101b88b1916ea27b597cfd45caf815acd0d369d625e56b1787557c6",
        "d800b786f43a8b2c2cc51451ec7dc67e04b935872b627ca5fdc15860156cbc6f"
      ],
      "status": "PASS",
      "vector_id": "I06-V01"
    },
    {
      "aggregate_reference_digest": "939b38407ac51adb91dba89dc215c97a526b5c0950a1cc6d19d7f8edf3cc2437",
      "ceremony_digest": "3fb99071a2d58a5b0aa9c111dc702d68726ba7382222552359dadbc544122488",
      "decryption_record_digest": "ecfd9da7f3d9d719f72f5c26a0dfadac67672f4169abef6329a49a542997b0ef",
      "plaintext_tally_digest": "580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c",
      "share_digests": [
        "1368ba64d215cb29eeb9b3422f85e152be6d294e0aadaf7072ec7a309928c707",
        "03f43be1e984df644a89d4010d5e5063b50bdb824be7670075f35e1ec83d5981",
        "dd82759355846d827b841e456bdeebcca94b9c64a738f191c0712480d3a5cf78",
        "6ec1f9f8957331ce2854e2458ffa7c22bea6e5f0cfbfac990df664374ff56228",
        "4fbd340cdd6fc5e952772d38c81f9823370e613dd0fa4c4e3623372329a74e61"
      ],
      "status": "PASS",
      "vector_id": "I06-V02"
    },
    {
      "aggregate_reference_digest": "939b38407ac51adb91dba89dc215c97a526b5c0950a1cc6d19d7f8edf3cc2437",
      "ceremony_digest": "3fb99071a2d58a5b0aa9c111dc702d68726ba7382222552359dadbc544122488",
      "decryption_record_digest": "ecfd9da7f3d9d719f72f5c26a0dfadac67672f4169abef6329a49a542997b0ef",
      "plaintext_tally_digest": "580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c",
      "share_digests": [
        "1368ba64d215cb29eeb9b3422f85e152be6d294e0aadaf7072ec7a309928c707",
        "03f43be1e984df644a89d4010d5e5063b50bdb824be7670075f35e1ec83d5981",
        "dd82759355846d827b841e456bdeebcca94b9c64a738f191c0712480d3a5cf78",
        "6ec1f9f8957331ce2854e2458ffa7c22bea6e5f0cfbfac990df664374ff56228",
        "4fbd340cdd6fc5e952772d38c81f9823370e613dd0fa4c4e3623372329a74e61"
      ],
      "status": "PASS",
      "vector_id": "I06-V03"
    },
    {
      "aggregate_reference_digest": "7e6beffefc73c8103d2dab246bce4651a9bcc5330b081a533cadc6b792c45837",
      "ceremony_digest": "56f267a4f7b97af768eb4b77ab108bf5b4a4ae7ffa351bd893c801363889d304",
      "decryption_record_digest": "7b9f3a94f276b8cd2eca2c896033b79b4437d473ea8d69bef37e01478be3d541",
      "plaintext_tally_digest": "34ed65c6fe5fe649af9223803d39b30259c000b9f5605503a39c7259ab7eedda",
      "share_digests": [
        "73db7641fc3480b46ee96f2349940de36636469e4337083bf55d6ac99752b8a0",
        "ce32e3e19d789b0f223362bf89e4e436dbbd711a3952103a52efb95d8fcd8c05",
        "48e87b31369825242c875ee76392b0cee06fe71493c54471904f5c0c02f1e2f7"
      ],
      "status": "PASS",
      "vector_id": "I06-V04"
    }
  ],
  "verifier": "independent-go-reference-b",
  "wraps_verifier_a": false
}
{
  "schema_version": "epd2.pb01.i06-final-validation/1",
  "checks": {
    "required_docs": true,
    "four_vectors": true,
    "nine_mutation_vectors": true,
    "local_i06_tests": true,
    "guardian_side_keygen_reference": true,
    "verifier_a": true,
    "verifier_b": true,
    "predecessor_protected_byte_preserved": true,
    "predecessor_semantic_regression_free": true,
    "i05_corrective_present": true,
    "no_guardian_private_key_files": true,
    "postgres_runtime_executed": true
  },
  "outcome": "Outcome A — I06 ESTABLISHED",
  "status": "PASS_WITH_CLASSIFICATION"
}
```

## PostgreSQL 16 log
```text
postgres (PostgreSQL) 16.14 (Ubuntu 16.14-1.pgdg24.04+1)
waiting for server to start.... done
server started
I06/PG class tamper-and-roles: PostgreSQL 16.x fresh cluster on port 56610; migrations 001-008 applied
TAP version 13
# (node:4001) ExperimentalWarning: SQLite is an experimental feature and might change at any time
# (Use `node --trace-warnings ...` to show where the warning was created)
# Subtest: I06/PG mandatory I05 corrective detects privileged aggregate-byte-only rewrite and decryption refuses
ok 1 - I06/PG mandatory I05 corrective detects privileged aggregate-byte-only rewrite and decryption refuses
  ---
  duration_ms: 1080.944894
  type: 'test'
  ...
# Subtest: I06/PG privileged tamper: guardian public key after freeze is detected
ok 2 - I06/PG privileged tamper: guardian public key after freeze is detected
  ---
  duration_ms: 547.495865
  type: 'test'
  ...
# Subtest: I06/PG privileged tamper: threshold after ceremony freeze is detected
ok 3 - I06/PG privileged tamper: threshold after ceremony freeze is detected
  ---
  duration_ms: 527.58566
  type: 'test'
  ...
# Subtest: I06/PG privileged tamper: frozen guardian-set member replacement is detected
ok 4 - I06/PG privileged tamper: frozen guardian-set member replacement is detected
  ---
  duration_ms: 521.007149
  type: 'test'
  ...
# Subtest: I06/PG privileged tamper: partial-decryption factor bytes are detected
ok 5 - I06/PG privileged tamper: partial-decryption factor bytes are detected
  ---
  duration_ms: 542.24118
  type: 'test'
  ...
# Subtest: I06/PG privileged tamper: partial-decryption proof bytes are detected
ok 6 - I06/PG privileged tamper: partial-decryption proof bytes are detected
  ---
  duration_ms: 595.646381
  type: 'test'
  ...
# Subtest: I06/PG privileged tamper: accepted share digest column is detected
ok 7 - I06/PG privileged tamper: accepted share digest column is detected
  ---
  duration_ms: 537.507527
  type: 'test'
  ...
# Subtest: I06/PG privileged tamper: aggregate digest alone is detected
ok 8 - I06/PG privileged tamper: aggregate digest alone is detected
  ---
  duration_ms: 508.953701
  type: 'test'
  ...
# Subtest: I06/PG privileged tamper: final plaintext bytes are detected
ok 9 - I06/PG privileged tamper: final plaintext bytes are detected
  ---
  duration_ms: 539.864579
  type: 'test'
  ...
# Subtest: I06/PG privileged tamper: final decryption-record digest is detected
ok 10 - I06/PG privileged tamper: final decryption-record digest is detected
  ---
  duration_ms: 545.180345
  type: 'test'
  ...
# Subtest: I06/PG roles enforce coordinator/ingester/finalizer/runtime separation
ok 11 - I06/PG roles enforce coordinator/ingester/finalizer/runtime separation
  ---
  duration_ms: 550.21297
  type: 'test'
  ...
1..11
# tests 11
# suites 0
# pass 11
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 6634.148046
I06/PG class tamper-and-roles: 11/11 PASS
waiting for server to start.... done
server started
I06/PG class concurrency-and-crash: PostgreSQL 16.x fresh cluster on port 56611; migrations 001-008 applied
TAP version 13
# (node:4640) ExperimentalWarning: SQLite is an experimental feature and might change at any time
# (Use `node --trace-warnings ...` to show where the warning was created)
# Subtest: I06/PG concurrent final threshold shares converge to one immutable record
ok 1 - I06/PG concurrent final threshold shares converge to one immutable record
  ---
  duration_ms: 1126.0095
  type: 'test'
  ...
# Subtest: I06/PG same-guardian concurrent duplicate race never double-counts threshold
ok 2 - I06/PG same-guardian concurrent duplicate race never double-counts threshold
  ---
  duration_ms: 430.739993
  type: 'test'
  ...
# Subtest: I06/PG CRASH-01 retry deterministically converges
ok 3 - I06/PG CRASH-01 retry deterministically converges
  ---
  duration_ms: 819.523188
  type: 'test'
  ...
# Subtest: I06/PG CRASH-02 retry deterministically converges
ok 4 - I06/PG CRASH-02 retry deterministically converges
  ---
  duration_ms: 660.003639
  type: 'test'
  ...
# Subtest: I06/PG CRASH-03 retry deterministically converges
ok 5 - I06/PG CRASH-03 retry deterministically converges
  ---
  duration_ms: 810.908156
  type: 'test'
  ...
# Subtest: I06/PG CRASH-04 retry deterministically converges
ok 6 - I06/PG CRASH-04 retry deterministically converges
  ---
  duration_ms: 692.783452
  type: 'test'
  ...
1..6
# tests 6
# suites 0
# pass 6
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 4672.586028
I06/PG class concurrency-and-crash: 6/6 PASS
waiting for server to start.... done
server started
I06/PG class ceremony-and-threshold: PostgreSQL 16.x fresh cluster on port 56612; migrations 001-008 applied
TAP version 13
# (node:5140) ExperimentalWarning: SQLite is an experimental feature and might change at any time
# (Use `node --trace-warnings ...` to show where the warning was created)
# Subtest: I06/PG real threshold ceremony freezes immutable N=3 T=2 public context
ok 1 - I06/PG real threshold ceremony freezes immutable N=3 T=2 public context
  ---
  duration_ms: 708.429422
  type: 'test'
  ...
# Subtest: I06/PG T-1 exposes no plaintext; exact threshold commits one immutable result; extra valid share cannot change plaintext
ok 2 - I06/PG T-1 exposes no plaintext; exact threshold commits one immutable result; extra valid share cannot change plaintext
  ---
  duration_ms: 911.693961
  type: 'test'
  ...
# Subtest: I06/PG duplicate guardian and malformed/invalid share fail closed
ok 3 - I06/PG duplicate guardian and malformed/invalid share fail closed
  ---
  duration_ms: 545.798534
  type: 'test'
  ...
1..3
# tests 3
# suites 0
# pass 3
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 2292.723883
I06/PG class ceremony-and-threshold: 3/3 PASS
waiting for server to start.... done
server started
I06/PG class restart-and-backup: PostgreSQL 16.x fresh cluster on port 56613; migrations 001-008 applied
TAP version 13
# (node:5403) ExperimentalWarning: SQLite is an experimental feature and might change at any time
# (Use `node --trace-warnings ...` to show where the warning was created)
# Subtest: I06/PG hard database crash/restart preserves same immutable plaintext and record digest
ok 1 - I06/PG hard database crash/restart preserves same immutable plaintext and record digest
  ---
  duration_ms: 1405.194932
  type: 'test'
  ...
# Subtest: I06/PG backup/restore preserves exact public ceremony/share/decryption evidence and no private guardian columns exist
ok 2 - I06/PG backup/restore preserves exact public ceremony/share/decryption evidence and no private guardian columns exist
  ---
  duration_ms: 1074.611236
  type: 'test'
  ...
1..2
# tests 2
# suites 0
# pass 2
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 2598.779102
I06/PG class restart-and-backup: 2/2 PASS
PB01-I06 PostgreSQL acceptance: 22/22 PASS
```
