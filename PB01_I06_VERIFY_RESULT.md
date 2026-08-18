# PB01-I06 External PostgreSQL Verification Result

**Verdict:** NOT VERIFIED

- Workflow run: 32177721191
- Commit: 4944160ecb2122101c305e37969b0a5a9f6416d0
- Candidate: `EPD2_VCRYPTO-PB01-I06_GUARDIAN_CEREMONY_AND_THRESHOLD_DECRYPTION_CANDIDATE_0.2_C1.zip`
- Expected SHA-256: `25114f10c95664e5145e4efc7c381aba4a2d9c3edc83760ee5e9bc72e55c532e`
- Integrity rc: 0
- Dependency install rc: 0
- Crypto/verifier rc: 0
- PostgreSQL 16 rc: 3

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

added 17 packages, and audited 18 packages in 2s

found 0 vulnerabilities
```

## Crypto / verifier log (tail)
```text

> epd2-pb01-i06-candidate@0.1.0 validate:i06
> npm run test:i06 && npm run verify:i06:a && npm run verify:i06:b && node scripts/i06_final_validate.mjs


> epd2-pb01-i06-candidate@0.1.0 test:i06
> node --test --test-concurrency=1 tests/i06-i05-corrective.test.mjs tests/i06-vectors.test.mjs tests/i06-mutation-vectors.test.mjs tests/i06-threshold-negatives.test.mjs tests/i06-api-boundary.test.mjs tests/i06-static-security.test.mjs

✔ I06 API never accepts caller-selected aggregate/ciphertext input (121.322853ms)
✔ I05 corrective recomputes digest from persisted aggregate bytes and I06 refuses byte-only mutation before ceremony access (191.996363ms)
✔ stale/unauthorized I05 tally cannot enter guardian/decryption path (0.481502ms)
✔ I06-N01 frozen mutation vector rejects (5.584775ms)
✔ I06-N02 frozen mutation vector rejects (1.42747ms)
✔ I06-N03 frozen mutation vector rejects (1.144562ms)
✔ I06-N04 frozen mutation vector rejects (44.818925ms)
✔ I06-N05 frozen mutation vector rejects (40.582919ms)
✔ I06-N06 frozen mutation vector rejects (36.941497ms)
✔ I06-N07 frozen mutation vector rejects (1.194145ms)
✔ I06-N08 frozen mutation vector rejects (0.935382ms)
✔ I06-N09 frozen mutation vector rejects (0.733044ms)
✔ candidate contains no guardian private key material or decryption/admin secret API (26.517214ms)
✔ I06 source has no plaintext result before threshold API route and no arbitrary aggregate input surface (1.095529ms)
✔ mutation negatives: wrong aggregate/election/guardian/digests/plaintext/record fail closed (2.93663ms)
✔ T-1 share has no Belenios plaintext result (34.613251ms)
✔ invalid proof among threshold shares is rejected by pinned upstream Belenios (40.115258ms)
✔ duplicate guardian cannot form threshold (38.817926ms)
✔ I06-V01 real Belenios threshold vector verifies (142.12832ms)
✔ I06-V02 real Belenios threshold vector verifies (193.667032ms)
✔ I06-V03 real Belenios threshold vector verifies (194.105946ms)
✔ I06-V04 real Belenios threshold vector verifies (117.915937ms)
✔ N=5 T=3 different valid threshold subsets and all five give identical plaintext (236.119345ms)
ℹ tests 23
ℹ suites 0
ℹ pass 23
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2097.703603

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
I06/PG class tamper-and-roles: PostgreSQL 16.x fresh cluster on port 57827; migrations 001-008 applied
✔ I06/PG mandatory I05 corrective detects privileged aggregate-byte-only rewrite and decryption refuses (1078.248591ms)
✔ I06/PG privileged tamper: guardian public key after freeze is detected (524.400224ms)
✔ I06/PG privileged tamper: threshold after ceremony freeze is detected (502.312912ms)
✔ I06/PG privileged tamper: frozen guardian-set member replacement is detected (497.310343ms)
✔ I06/PG privileged tamper: partial-decryption factor bytes are detected (552.182959ms)
✔ I06/PG privileged tamper: partial-decryption proof bytes are detected (538.340151ms)
✔ I06/PG privileged tamper: accepted share digest column is detected (529.552989ms)
✔ I06/PG privileged tamper: aggregate digest alone is detected (521.653756ms)
✔ I06/PG privileged tamper: final plaintext bytes are detected (519.098892ms)
✔ I06/PG privileged tamper: final decryption-record digest is detected (520.026112ms)
✔ I06/PG roles enforce coordinator/ingester/finalizer/runtime separation (654.573765ms)
ℹ tests 11
ℹ suites 0
ℹ pass 11
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 6580.579241
I06/PG class tamper-and-roles: expected 11/11 PASS; got tests=0 pass=0 fail=0
```
