# PB01-I07 C1 Verification Result

**Verdict:** PASS — PB01-I07 C1 external PostgreSQL gate passed

- Workflow run: 32193529723
- Commit: 9016ec565c1516eaae4fc17e9c2940ab9760607d
- Candidate: `EPD2_VCRYPTO-PB01-I07_PUBLIC_RESULT_EVIDENCE_AND_INDEPENDENT_E2E_VERIFICATION_CANDIDATE_0.2_C1.zip`
- Expected SHA256: `32d5026f5398ea867997e6fddd472bf7eb59e636612a021864f4a07031d70c79`
- Node: `v24.19.0`
- Go: `go version go1.23.12 linux/amd64`
- PostgreSQL: `postgres (PostgreSQL) 16.14 (Ubuntu 16.14-1.pgdg24.04+1)`
- Integrity rc: 0
- Dependency install rc: 0
- Packaged-evidence rejection rc: 2 (non-zero required)
- PostgreSQL 16 live gate rc: 0
- validate:i07 rc: 0

## PostgreSQL log tail
```text

> epd2-pb01-i06-candidate@0.1.0 test:i07:postgres
> bash scripts/run_i07_postgres_validation.sh

postgres (PostgreSQL) 16.14 (Ubuntu 16.14-1.pgdg24.04+1)
Node.js v24.19.0
waiting for server to start.... done
server started
I07/PG class publication-and-roles: fresh PostgreSQL 16 cluster; migrations 001-010
✔ I07/PG real persistence path publishes one final bundle independently verified by A and B (8715.341458ms)
✔ I07/PG concurrent publishers converge to one immutable canonical result (986.251321ms)
✔ I07/PG idempotent retry returns same result and conflicting direct commit is rejected (934.453008ms)
✔ I07/PG least privilege: publisher has only scoped I07 write + I06 authority read; public verifier is read-only FINAL view (734.37467ms)
ℹ tests 4
ℹ suites 0
ℹ pass 4
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 11527.400569
I07/PG class publication-and-roles: 4/4 PASS
waiting for server to start.... done
server started
I07/PG class crash-consistency: fresh PostgreSQL 16 cluster; migrations 001-010
✔ I07/PG crash before_result_persistence leaves no incomplete FINAL and retry converges (1573.433495ms)
✔ I07/PG crash after_result_persistence_before_evidence_publication_marker leaves no incomplete FINAL and retry converges (1304.188859ms)
✔ I07/PG crash after_evidence_persistence_before_final_status_transition leaves no incomplete FINAL and retry converges (1136.878678ms)
✔ I07/PG crash immediately after FINAL commit before response preserves one final result and retry is idempotent (1136.726738ms)
ℹ tests 4
ℹ suites 0
ℹ pass 4
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 5283.805409
I07/PG class crash-consistency: 4/4 PASS
waiting for server to start.... done
server started
I07/PG class privileged-tamper: fresh PostgreSQL 16 cluster; migrations 001-010
✔ I07/PG privileged tamper aggregate bytes is detected independently of DB permissions (1198.357562ms)
✔ I07/PG privileged tamper guardian public key is detected independently of DB permissions (782.412417ms)
✔ I07/PG privileged tamper threshold is detected independently of DB permissions (757.944511ms)
✔ I07/PG privileged tamper accepted share artifact is detected independently of DB permissions (777.806745ms)
✔ I07/PG privileged tamper accepted share digest is detected independently of DB permissions (789.892425ms)
✔ I07/PG privileged tamper plaintext bytes is detected independently of DB permissions (786.0979ms)
✔ I07/PG privileged tamper plaintext digest is detected independently of DB permissions (777.913603ms)
✔ I07/PG privileged tamper decryption record canonical is detected independently of DB permissions (809.148693ms)
✔ I07/PG privileged tamper public result canonical bytes is detected independently of DB permissions (935.589183ms)
✔ I07/PG privileged tamper public result digest column is detected independently of DB permissions (928.095392ms)
ℹ tests 10
ℹ suites 0
ℹ pass 10
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 8688.674178
I07/PG class privileged-tamper: 10/10 PASS
waiting for server to start.... done
server started
I07/PG class restart-and-backup: fresh PostgreSQL 16 cluster; migrations 001-010
✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (2201.468872ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1692.998248ms)
ℹ tests 2
ℹ suites 0
ℹ pass 2
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 4022.514869
I07/PG class restart-and-backup: 2/2 PASS
PB01-I07 PostgreSQL acceptance: 20/20 PASS
```

## validate:i07 log tail
```text
      "status": "REJECT",
      "reason": "I06_RECORD"
    },
    {
      "mutation_id": "I07-N18",
      "status": "REJECT",
      "reason": "I06_RECORD"
    },
    {
      "mutation_id": "I07-N19",
      "status": "REJECT",
      "reason": "I06_RECORD"
    },
    {
      "mutation_id": "I07-N20",
      "status": "REJECT",
      "reason": "I06_RECORD"
    },
    {
      "mutation_id": "I07-N21",
      "status": "REJECT",
      "reason": "I07_RESULT_BIND"
    },
    {
      "mutation_id": "I07-N22",
      "status": "REJECT",
      "reason": "I07_ELECTION_CROSS_BIND"
    },
    {
      "mutation_id": "I07-N23",
      "status": "REJECT",
      "reason": "I07_RESULT_BIND"
    },
    {
      "mutation_id": "I07-N24",
      "status": "REJECT",
      "reason": "I06_RECORD_CEREMONY"
    },
    {
      "mutation_id": "I07-N25",
      "status": "REJECT",
      "reason": "PANIC_REJECT:expected array"
    },
    {
      "mutation_id": "I07-N26",
      "status": "REJECT",
      "reason": "I07_SCHEMA"
    }
  ],
  "mutations_rejected": "26",
  "producer_imports": false,
  "schema_version": "epd2.pb01.i07-verifier-b-result/1",
  "status": "PASS",
  "vector_count": "4",
  "vector_results": [
    {
      "vector_id": "I07-V01",
      "status": "PASS",
      "election_digest": "3a4b152f2f34b9f78318619b64c5d282d5d497ba9cb3a01618fadac6162d3d27",
      "final_set_reference": "4d33ca52ac94a90c22049dc017e7a69a53dbbd7211308c54722383d6753605d1",
      "aggregate_digest": "5e295e8fd222a03b5c50d1b1bf7188620bf8db38f986f25c55a8793a2c094679",
      "ceremony_digest": "349223d8a1a59fe480d6774df7c08912c0d2dd2df64f73ca7ec719ead0c35236",
      "share_digests": [
        "e56f69730ed30a8530a78352d861f937a76d12cd8996d9c0f1641bd067da24f7",
        "ef5fee15828ba66192a6f2480edd8ba83a61361fd3da8bd76b9f640ff0aa6d40"
      ],
      "plaintext_tally_digest": "580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c",
      "decryption_record_digest": "ab25b78657494d96c6e303242512bd8c316cc35793dfd9f838d513c33135baae",
      "public_result_digest": "550ed2b41b465f71b615ce3805cfb884a2f6d16f9780b8bad96694a5718b001e",
      "public_evidence_bundle_digest": "d15194b1bb5c8ad10e8cf9402c9c8b1dcd0fc575597f583e5121c70b712fa0cc"
    },
    {
      "vector_id": "I07-V02",
      "status": "PASS",
      "election_digest": "3a4b152f2f34b9f78318619b64c5d282d5d497ba9cb3a01618fadac6162d3d27",
      "final_set_reference": "4d33ca52ac94a90c22049dc017e7a69a53dbbd7211308c54722383d6753605d1",
      "aggregate_digest": "5e295e8fd222a03b5c50d1b1bf7188620bf8db38f986f25c55a8793a2c094679",
      "ceremony_digest": "349223d8a1a59fe480d6774df7c08912c0d2dd2df64f73ca7ec719ead0c35236",
      "share_digests": [
        "e56f69730ed30a8530a78352d861f937a76d12cd8996d9c0f1641bd067da24f7",
        "ef5fee15828ba66192a6f2480edd8ba83a61361fd3da8bd76b9f640ff0aa6d40",
        "d19e010be386dd735c96a0ba444aabbea6d6d5865227c3e01f1dd26860b34d4b"
      ],
      "plaintext_tally_digest": "580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c",
      "decryption_record_digest": "ab25b78657494d96c6e303242512bd8c316cc35793dfd9f838d513c33135baae",
      "public_result_digest": "550ed2b41b465f71b615ce3805cfb884a2f6d16f9780b8bad96694a5718b001e",
      "public_evidence_bundle_digest": "1466f5c6479911da060f642d4fba08424703c7380d4aa2cb154be315d2d6f2da"
    },
    {
      "vector_id": "I07-V03",
      "status": "PASS",
      "election_digest": "3a4b152f2f34b9f78318619b64c5d282d5d497ba9cb3a01618fadac6162d3d27",
      "final_set_reference": "4d33ca52ac94a90c22049dc017e7a69a53dbbd7211308c54722383d6753605d1",
      "aggregate_digest": "5e295e8fd222a03b5c50d1b1bf7188620bf8db38f986f25c55a8793a2c094679",
      "ceremony_digest": "349223d8a1a59fe480d6774df7c08912c0d2dd2df64f73ca7ec719ead0c35236",
      "share_digests": [
        "e56f69730ed30a8530a78352d861f937a76d12cd8996d9c0f1641bd067da24f7",
        "ef5fee15828ba66192a6f2480edd8ba83a61361fd3da8bd76b9f640ff0aa6d40",
        "d19e010be386dd735c96a0ba444aabbea6d6d5865227c3e01f1dd26860b34d4b"
      ],
      "plaintext_tally_digest": "580739f19efc3cd5938101ffe1a4e074716a45e9c4112ad298b2127f82f4769c",
      "decryption_record_digest": "ab25b78657494d96c6e303242512bd8c316cc35793dfd9f838d513c33135baae",
      "public_result_digest": "550ed2b41b465f71b615ce3805cfb884a2f6d16f9780b8bad96694a5718b001e",
      "public_evidence_bundle_digest": "1466f5c6479911da060f642d4fba08424703c7380d4aa2cb154be315d2d6f2da"
    },
    {
      "vector_id": "I07-V04",
      "status": "PASS",
      "election_digest": "b99461b29f37a7ccc4c1022f88bd7add2fe61482fa7c3a276c4aaf5348367955",
      "final_set_reference": "3de669d8adc92f417919af7d9ba9691945a83e5171844d34c15a49805d6243d6",
      "aggregate_digest": "7e6beffefc73c8103d2dab246bce4651a9bcc5330b081a533cadc6b792c45837",
      "ceremony_digest": "56f267a4f7b97af768eb4b77ab108bf5b4a4ae7ffa351bd893c801363889d304",
      "share_digests": [
        "5e4a20157d368cdbf66fea465e53886a01f6710aa0915e19f2cd38b4b82cccec",
        "81d81fe34a500c186c2a68d2337fcb029c994951d46b74e30a7afae05a5435b1"
      ],
      "plaintext_tally_digest": "34ed65c6fe5fe649af9223803d39b30259c000b9f5605503a39c7259ab7eedda",
      "decryption_record_digest": "6cab8be2cf8f4db1024d1ba78168924b74f77f1008cc18b855b44b3c1c03e8ad",
      "public_result_digest": "2b1de73c9d19a3bdaa9cd2248e440dd4ae40f7c50f9e01fbbb3db87fdb8f6978",
      "public_evidence_bundle_digest": "2f9ac3d8805b27941c35918f663dde7a17f12a49fe22a7f106319d991e871748"
    }
  ],
  "verifier": "independent-go-verifier-b",
  "wraps_verifier_a": false
}

[I07 current-run] npm run verify:i07:agreement

> epd2-pb01-i06-candidate@0.1.0 verify:i07:agreement
> node scripts/i07_cross_language_agreement.mjs

{"schema_version":"epd2.pb01.i07-cross-language-agreement/1","verifier_a":"independent-node-verifier-a","verifier_b":"independent-go-verifier-b","vector_count":"4","vector_results":[{"vector_id":"I07-V01","byte_for_byte_agreement":true,"fields":["election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest","status"]},{"vector_id":"I07-V02","byte_for_byte_agreement":true,"fields":["election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest","status"]},{"vector_id":"I07-V03","byte_for_byte_agreement":true,"fields":["election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest","status"]},{"vector_id":"I07-V04","byte_for_byte_agreement":true,"fields":["election_digest","final_set_reference","aggregate_digest","ceremony_digest","share_digests","plaintext_tally_digest","decryption_record_digest","public_result_digest","public_evidence_bundle_digest","status"]}],"byte_for_byte_agreement":true,"status":"PASS"}

[I07 current-run] /opt/hostedtoolcache/node/24.19.0/x64/bin/node scripts/i07_check_predecessor.mjs
{"schema_version":"epd2.pb01.i07-predecessor-regression/1","predecessor_filename":"EPD2_VCRYPTO-PB01-I06_GUARDIAN_CEREMONY_AND_THRESHOLD_DECRYPTION_CANDIDATE_0.2_C1.zip","predecessor_archive_sha256":"25114f10c95664e5145e4efc7c381aba4a2d9c3edc83760ee5e9bc72e55c532e","predecessor_file_count":547,"checked_files":547,"exact_byte_matches":545,"allowed_packaging_only_modifications":["package.json","SHA256SUMS.txt"],"unauthorized_modified_files":[],"missing_predecessor_files":[],"package_lock_byte_identical":true,"foreign_election_ballot_guard_byte_identical":true,"i06_c1_election_ballot_binding_helper_byte_identical":true,"semantic_predecessor_changes":0,"status":"PASS"}

[I07 current-run] /opt/hostedtoolcache/node/24.19.0/x64/bin/node scripts/i07_final_validate.mjs
{
  "schema_version": "epd2.pb01.i07-final-validation/2",
  "invocation_id": "i07-standalone-e9577703ca3f74f56f8cab280615fb6f3dfb255140ef03bc7c3bf4b9c17aa66f",
  "postgresql_attestation_errors": [],
  "checks": {
    "required_docs": true,
    "positive_vectors": true,
    "mutation_vectors": true,
    "verifier_a": true,
    "verifier_b": true,
    "cross_language": true,
    "postgres_16_node_24_19": true,
    "predecessor_regression": true,
    "dependencies_unchanged": true,
    "offline_verification_commands": true,
    "no_guardian_private_material": true,
    "no_universal_authority": true,
    "non_binding_pilot": true
  },
  "private_files": [],
  "status": "PASS",
  "outcome": "PB01-I07 — ACCEPTED / Outcome A — I07 ESTABLISHED"
}
```
