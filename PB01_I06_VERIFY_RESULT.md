# PB01-I06 External PostgreSQL Verification Result

**Verdict:** NOT VERIFIED

- Workflow run: 32177601775
- Commit: d76549a8cb0ae0f5d16cb8dc1996d190aaa8ffc0
- Candidate: `EPD2_VCRYPTO-PB01-I06_GUARDIAN_CEREMONY_AND_THRESHOLD_DECRYPTION_CANDIDATE_0.1.zip`
- Expected SHA-256: `1f81f7f1193e92ffbb60be75b0b4ebc3f8c2879a6a4407c425a9a77426dc30be`
- Integrity rc: 1
- Dependency install rc: 1
- Crypto/verifier rc: 1
- PostgreSQL 16 rc: 127

## Integrity log (tail)
```text
candidate=EPD2_VCRYPTO-PB01-I06_GUARDIAN_CEREMONY_AND_THRESHOLD_DECRYPTION_CANDIDATE_0.1.zip
sha256sum: EPD2_VCRYPTO-PB01-I06_GUARDIAN_CEREMONY_AND_THRESHOLD_DECRYPTION_CANDIDATE_0.1.zip: No such file or directory
actual_sha256=
expected_sha256=1f81f7f1193e92ffbb60be75b0b4ebc3f8c2879a6a4407c425a9a77426dc30be
unzip:  cannot find or open EPD2_VCRYPTO-PB01-I06_GUARDIAN_CEREMONY_AND_THRESHOLD_DECRYPTION_CANDIDATE_0.1.zip, EPD2_VCRYPTO-PB01-I06_GUARDIAN_CEREMONY_AND_THRESHOLD_DECRYPTION_CANDIDATE_0.1.zip.zip or EPD2_VCRYPTO-PB01-I06_GUARDIAN_CEREMONY_AND_THRESHOLD_DECRYPTION_CANDIDATE_0.1.zip.ZIP.
root_dirs=0
sha256sum: SHA256SUMS.txt: No such file or directory
```

## Dependency log (tail)
```text
npm error code ENOTCACHED
npm error request to https://registry.npmjs.org/yocto-queue/-/yocto-queue-0.1.0.tgz failed: cache mode is 'only-if-cached' but no cached response is available.
npm error A complete log of this run can be found in: /home/runner/.npm/_logs/2026-08-18T19_37_24_587Z-debug-0.log
```

## Crypto / verifier log (tail)
```text
npm error Missing script: "validate:i06"
npm error
npm error To see a list of scripts, run:
npm error   npm run
npm error A complete log of this run can be found in: /home/runner/.npm/_logs/2026-08-18T19_37_29_117Z-debug-0.log
```

## PostgreSQL 16 log
```text
bash: scripts/run_i06_postgres_validation.sh: No such file or directory
```
