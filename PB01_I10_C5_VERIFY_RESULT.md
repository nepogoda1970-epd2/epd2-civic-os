# PB01-I10 C5 Final Acceptance Result

- Verdict: **FAIL**
- Workflow run: 32376339294
- Commit: 09d282b724b0e0c57d9d94ef74547b0ca7f63e41
- Candidate: EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5.zip
- Expected / reconstructed SHA-256: ae62868b7f67eba6e3e2652f03167c965f32653d788d190c1f5b067e1e53bb2c
- validate:i10 outcome: failure

## Validation progress tail
```text
✔ ledger detects modification, deletion, reordering and conflicting checkpoint (1916.991702ms)
✔ backup/restore preserves exact ballot bytes, ledger and private/public separation (559.810349ms)
✔ privacy-preserving storage and audit contain no selection, credential token or randomness (138.219069ms)
✔ CORS is exact, non-credentialed and arbitrary origin is rejected (52.475199ms)
✔ cheap invalid schema is rejected before native verification (29.661026ms)
✔ bounded limiter resets and cannot permanently lock out a legitimate client (0.868688ms)
✔ I03 submission authority exposes no crypto-finalization routes; I05 tally boundary remains separately authorized (7.787582ms)
✔ submission capability grants no election administration or ledger mutation authority (30.391497ms)
✔ strict parser accepts canonical JSON and rejects duplicate members (6.494516ms)
✔ ledger domain is deterministic and commits order/link fields (1.658429ms)
✔ scoped capability is election-bound, expiring and yields opaque lifecycle handle (2.708303ms)
✔ receipt uses independent Ed25519 key and verifies (3.213163ms)
ℹ tests 34
ℹ suites 0
ℹ pass 34
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2984.12415
[I10_PROGRESS] PASS label="regression:i03-core" elapsed_ms=3140
[I10_PROGRESS] START label="regression:i04" timeout_ms=300000

> epd2-pb01-i06-candidate@0.1.0 test:i04
> I09_PG_STAGE=i04 bash scripts/run_i09_postgres_class.sh tests/i04-policy.unit.test.mjs tests/i04-finalization.integration.test.mjs tests/i04-concurrency-crash.test.mjs tests/i04-tamper-backup-roles.test.mjs

✔ I04 concurrent identical and conflicting finalizers converge without split state (220.261463ms)
✔ I04-CRASH-01 is atomic and retry converges (143.565776ms)
✔ I04-CRASH-02 is atomic and retry converges (136.280839ms)
✔ I04-CRASH-03 is atomic and retry converges (132.821852ms)
✔ I04-CRASH-04 is atomic and retry converges (134.500132ms)
✔ I04 submission-versus-closure race has one deterministic boundary outcome (146.148882ms)
✔ I04 real I03 revote E2E selects latest valid, preserves history and exact bytes (256.731536ms)
✔ I04 multi-lifecycle resolution yields A2, B1 and C3 in I01 digest order (260.099893ms)
✔ I04 empty election finalizes deterministically (102.622197ms)
✔ latest-valid ordering is stable across input permutations (4.532862ms)
✔ missing or cross-election lifecycle binding fails closed (0.583195ms)
✔ I04 public verifier detects every committed-field tamper class (233.214939ms)
✔ I04 refuses finalization when I03 ledger integrity has been altered (156.724359ms)
✔ I04 PostgreSQL roles enforce submission/finalizer/evidence/migration separation (183.36426ms)
✔ I04 backup/restore preserves exact I03 history and identical final artifacts (515.599571ms)
ℹ tests 15
ℹ suites 0
ℹ pass 15
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3021.838376
[I10_PROGRESS] PASS label="regression:i04" elapsed_ms=4658
[I10_PROGRESS] START label="regression:i04-verifier-b" timeout_ms=120000

> epd2-pb01-i06-candidate@0.1.0 test:i04:verifier-b
> node --test tests/i04-cross-language-verifier.test.mjs

✔ I04 independent cross-language Verifier B consumes all frozen vectors and rejects required mutations (4732.827278ms)
✔ independent verifier source does not import producer hashing/canonicalization modules (2.171925ms)
ℹ tests 2
ℹ suites 0
ℹ pass 2
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 4795.444346
[I10_PROGRESS] PASS label="regression:i04-verifier-b" elapsed_ms=4943
[I10_PROGRESS] START label="regression:i05" timeout_ms=300000

> epd2-pb01-i06-candidate@0.1.0 test:i05
> node --test --test-concurrency=1 tests/i05-vectors.test.mjs tests/i05-api-boundary.test.mjs tests/i05-static-security.test.mjs tests/i05-crash-concurrency.test.mjs

✔ tally API accepts only election reference in path and rejects caller ballot arrays (49.357052ms)
✔ CRASH-01..04 retry converges and same tally concurrency is one logical record (529.243127ms)
✔ I05 adds no decryption/guardian secret material and SQL enforces role separation (9.899507ms)
✔ I05 real Belenios vectors and both verifier reports pass (6.3141ms)
✔ revote vector consumes only A2/B1/C3 and agrees with independent three-ballot aggregate (2.382848ms)
✔ empty final set has deterministic upstream identity aggregate (2.059255ms)
✔ real alternate aggregates and foreign ballot attacks are rejected (1.132028ms)
✔ independently encrypted/revoted ciphertexts remain distinct exact ballots (0.806222ms)
ℹ tests 8
ℹ suites 0
ℹ pass 8
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 885.441265
[I10_PROGRESS] PASS label="regression:i05" elapsed_ms=1035
[I10_PROGRESS] START label="regression:i06" timeout_ms=300000

> epd2-pb01-i06-candidate@0.1.0 test:i06
> node --test --test-concurrency=1 tests/i06-i05-corrective.test.mjs tests/i06-vectors.test.mjs tests/i06-mutation-vectors.test.mjs tests/i06-threshold-negatives.test.mjs tests/i06-api-boundary.test.mjs tests/i06-static-security.test.mjs

✔ I06 API never accepts caller-selected aggregate/ciphertext input (41.996114ms)
✔ I05 corrective recomputes digest from persisted aggregate bytes and I06 refuses byte-only mutation before ceremony access (126.283523ms)
✔ stale/unauthorized I05 tally cannot enter guardian/decryption path (0.410374ms)
✔ I06-N01 frozen mutation vector rejects (6.097677ms)
✔ I06-N02 frozen mutation vector rejects (1.634154ms)
✔ I06-N03 frozen mutation vector rejects (1.370833ms)
✔ I06-N04 frozen mutation vector rejects (43.832032ms)
✔ I06-N05 frozen mutation vector rejects (40.500281ms)
✔ I06-N06 frozen mutation vector rejects (38.342493ms)
✔ I06-N07 frozen mutation vector rejects (1.212508ms)
✔ I06-N08 frozen mutation vector rejects (1.10793ms)
✔ I06-N09 frozen mutation vector rejects (0.788749ms)
✔ candidate contains no guardian private key material or decryption/admin secret API (78.918924ms)
✔ I06 source has no plaintext result before threshold API route and no arbitrary aggregate input surface (1.273907ms)
✔ mutation negatives: wrong aggregate/election/guardian/digests/plaintext/record fail closed (3.464022ms)
✔ T-1 share has no Belenios plaintext result (35.946352ms)
✔ invalid proof among threshold shares is rejected by pinned upstream Belenios (40.133216ms)
✔ duplicate guardian cannot form threshold (39.144023ms)
✔ I06-V01 real Belenios threshold vector verifies (139.81065ms)
✔ I06-V02 real Belenios threshold vector verifies (187.682304ms)
✔ I06-V03 real Belenios threshold vector verifies (189.173981ms)
✔ I06-V04 real Belenios threshold vector verifies (119.801568ms)
✔ N=5 T=3 different valid threshold subsets and all five give identical plaintext (241.393565ms)
ℹ tests 23
ℹ suites 0
ℹ pass 23
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1932.614428
[I10_PROGRESS] PASS label="regression:i06" elapsed_ms=2081
[I10_PROGRESS] START label="regression:i07" timeout_ms=300000

> epd2-pb01-i06-candidate@0.1.0 test:i07
> node --test --test-concurrency=1 tests/i07-vectors.test.mjs tests/i07-mutations.test.mjs tests/i07-offline.test.mjs tests/i07-static-security.test.mjs tests/i07-validation-harness.test.mjs

✔ Verifier A rejects all 26 frozen mutations (265.711717ms)
✔ mutation index is complete and unique (0.283167ms)
✔ I07 downloaded frozen bundle verifies offline with independent Verifier A (186.900157ms)
✔ I07 downloaded frozen bundle verifies offline with independent Go Verifier B (3209.356904ms)
✔ I07 public bundles contain no identity/private/analytics fields and remain NON_BINDING_PILOT (7.445086ms)
✔ I07 code introduces no universal authority and no guardian private-key files (244.770215ms)
✔ stale packaged PostgreSQL acceptance cannot satisfy a new validation invocation (1.790234ms)
✔ tampered PostgreSQL attestation binding is rejected (0.293016ms)
✔ current invocation 20/20 PostgreSQL 16 + exact Node attestation is accepted (0.871964ms)
✔ I07-V01 producer structural public bundle verification (8.313555ms)
✔ I07-V02 producer structural public bundle verification (6.757915ms)
✔ I07-V03 producer structural public bundle verification (3.347785ms)
✔ I07-V04 producer structural public bundle verification (2.55612ms)
✔ V01/V02/V03 publish byte-identical deterministic result (1.530961ms)
✔ V04 is deterministic zero tally (1.989645ms)
ℹ tests 15
ℹ suites 0
ℹ pass 15
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 4217.110192
[I10_PROGRESS] PASS label="regression:i07" elapsed_ms=4361
[I10_PROGRESS] START label="regression:i08" timeout_ms=300000

> epd2-pb01-i06-candidate@0.1.0 test:i08
> node --test --test-concurrency=1 tests/i08-release-hardening.test.mjs

✔ I08 exact Rust dependency declarations and pinned toolchain (6.731777ms)
✔ Cargo.lock and vendored offline closure are committed and governed (2.628285ms)
✔ I08 frozen positive and negative corpus remains 4 / 26 (2.155918ms)
✔ Rust verifier has no Node/Go/Belenios process execution dependency (0.995203ms)
✔ release hygiene fails closed on tmp and temporary leftovers (0.406798ms)
✔ validate:i08 pins exact Node and authorizes only fresh Rust build (1.689754ms)
✔ I08 commands are registered (0.870169ms)
✔ I08 verifier/release changes do not expand authority (2.039588ms)
✔ release profile fixes source, lock, toolchain and vector-set provenance (1.499417ms)
ℹ tests 9
ℹ suites 0
ℹ pass 9
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 83.260631
[I10_PROGRESS] PASS label="regression:i08" elapsed_ms=231
[I10_PROGRESS] START label="regression:i09" timeout_ms=300000

> epd2-pb01-i06-candidate@0.1.0 test:i09
> node --test --test-concurrency=1 tests/i09-retry-policy.test.mjs tests/i09-static-security.test.mjs

✔ I09 retry policy is exactly bounded 40001-only with deterministic backoff (1.689787ms)
✔ retryable 40001 converges to one canonical result within budget (31.434611ms)
✔ retry budget exhaustion is explicit and bounded (62.199564ms)
✔ non-retryable database 40P01 fails immediately (0.460497ms)
✔ non-retryable database 23505 fails immediately (0.367635ms)
✔ non-retryable database 08006 fails immediately (0.273049ms)
✔ FOREIGN_ELECTION_BALLOT is never retried (0.270344ms)
✔ FINAL_SET_MISMATCH is never retried (0.164787ms)
✔ TALLY_CONFLICT is never retried (0.260084ms)
✔ unbounded or broadened retry configuration is rejected fail-closed (0.430111ms)
✔ I09 C1 single-flight coalesces same-process same-store only (51.370469ms)
✔ I09 preserves I08 Rust source, Cargo.lock and exact toolchain (8.383843ms)
✔ I09 stale I03 tally route assertion is replaced by scoped security boundary (1.150613ms)
✔ I09 retry implementation cannot retry semantic/security failures (0.829164ms)
✔ I09 required commands are registered and validate:i09 is authoritative (1.497088ms)
✔ I09 archive hygiene and predecessor manifest are governed (2.734972ms)
✔ I09 C1 validate:i09 restores full I04 predecessor regression (1.012626ms)
✔ I09 C1 DB concurrency proof cannot pass through one coalesced store transaction (0.95472ms)
✔ I09 C1 real contention proof does not count manual RAISE as burst contention (1.017986ms)
✔ I09 C1 mixed-stage races are mandatory in validator evidence (1.075152ms)
✖ I09 C4 predecessor checker accepts exact cumulative diff including declared i05 helper change from pristine sealed candidate (1.114135ms)
✔ I09 C3 predecessor checker rejects genuinely undeclared changed file (48.701122ms)
✔ I09 C3 predecessor checker rejects undeclared added file (45.364207ms)
✔ I09 C3 predecessor checker rejects undeclared deletion (44.306878ms)
✔ I09 C3 agreement normalizes real Go/Rust vector_results wrappers for S1000/S10000 (40.31212ms)
✔ I09 C3 agreement rejects Go governed digest divergence (37.539835ms)
✔ I09 C3 agreement rejects Rust governed digest divergence (38.545211ms)
✔ I09 C3 agreement rejects missing governed field (39.48666ms)
✔ I09 C3 agreement rejects wrong vector result (36.920464ms)
✔ I09 C3 acceptance harness recognizes structural stale-evidence protection and governed PG tamper dependency (35.530989ms)
ℹ tests 30
ℹ suites 0
ℹ pass 29
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 676.030964

✖ failing tests:

test at tests/i09-static-security.test.mjs:19:1
✖ I09 C4 predecessor checker accepts exact cumulative diff including declared i05 helper change from pristine sealed candidate (1.114135ms)
  AssertionError [ERR_ASSERTION]: I09_CANDIDATE_ZIP is required for pristine predecessor isolation
      at TestContext.<anonymous> (file:///tmp/epd2-i10-cleanroom-OogkZx/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/tests/i09-static-security.test.mjs:21:10)
      at Test.runInAsyncScope (node:async_hooks:227:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Test.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Test.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: false,
    code: 'ERR_ASSERTION',
    actual: undefined,
    expected: true,
    operator: '==',
    diff: 'simple'
  }
[I10_PROGRESS] FAIL label="regression:i09" elapsed_ms=826 status=1
file:///tmp/epd2-i10-cleanroom-OogkZx/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_lib.mjs:12
export function run(cmd,args=[],opts={}){const cwd=opts.cwd??root;const timeoutMs=opts.timeoutMs??I10_TIMEOUTS.unit;const label=opts.label??`${cmd} ${args.join(' ')}`;const started=Date.now();console.log(`[I10_PROGRESS] START label=${JSON.stringify(label)} timeout_ms=${timeoutMs}`);const common={cwd,env:{...process.env,...opts.env},encoding:'utf8',stdio:opts.capture?'pipe':'inherit',maxBuffer:128*1024*1024};let r;if(process.platform==='linux'){const seconds=Math.max(1,Math.ceil(timeoutMs/1000));r=spawnSync('timeout',['--signal=TERM','--kill-after=10s',`${seconds}s`,cmd,...args],common);}else{r=spawnSync(cmd,args,{...common,timeout:timeoutMs,killSignal:'SIGKILL'});}const elapsed=Date.now()-started;const timedOut=(process.platform==='linux'&&r.status===124)||r.error?.code==='ETIMEDOUT';if(timedOut){console.error(`[I10_PROGRESS] TIMEOUT label=${JSON.stringify(label)} elapsed_ms=${elapsed} timeout_ms=${timeoutMs}`);throw new Error(`COMMAND_TIMEOUT:${label}:${timeoutMs}`);}if(r.error){console.error(`[I10_PROGRESS] ERROR label=${JSON.stringify(label)} elapsed_ms=${elapsed} code=${r.error.code??'UNKNOWN'}`);throw r.error;}if(r.status!==0){console.error(`[I10_PROGRESS] FAIL label=${JSON.stringify(label)} elapsed_ms=${elapsed} status=${r.status}`);throw new Error(`COMMAND_FAILED:${label}:${r.status}${opts.capture?`\n${r.stdout}\n${r.stderr}`:''}`);}console.log(`[I10_PROGRESS] PASS label=${JSON.stringify(label)} elapsed_ms=${elapsed}`);return r;}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            

Error: COMMAND_FAILED:regression:i09:1
    at run (file:///tmp/epd2-i10-cleanroom-OogkZx/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_lib.mjs:12:1266)
    at file:///tmp/epd2-i10-cleanroom-OogkZx/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_validate_worker.mjs:29:4

Node.js v24.19.0
[I10_PROGRESS] FAIL label="worker:full-i10" elapsed_ms=22274 status=1
file:///tmp/pb01-i10-c5/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_lib.mjs:12
export function run(cmd,args=[],opts={}){const cwd=opts.cwd??root;const timeoutMs=opts.timeoutMs??I10_TIMEOUTS.unit;const label=opts.label??`${cmd} ${args.join(' ')}`;const started=Date.now();console.log(`[I10_PROGRESS] START label=${JSON.stringify(label)} timeout_ms=${timeoutMs}`);const common={cwd,env:{...process.env,...opts.env},encoding:'utf8',stdio:opts.capture?'pipe':'inherit',maxBuffer:128*1024*1024};let r;if(process.platform==='linux'){const seconds=Math.max(1,Math.ceil(timeoutMs/1000));r=spawnSync('timeout',['--signal=TERM','--kill-after=10s',`${seconds}s`,cmd,...args],common);}else{r=spawnSync(cmd,args,{...common,timeout:timeoutMs,killSignal:'SIGKILL'});}const elapsed=Date.now()-started;const timedOut=(process.platform==='linux'&&r.status===124)||r.error?.code==='ETIMEDOUT';if(timedOut){console.error(`[I10_PROGRESS] TIMEOUT label=${JSON.stringify(label)} elapsed_ms=${elapsed} timeout_ms=${timeoutMs}`);throw new Error(`COMMAND_TIMEOUT:${label}:${timeoutMs}`);}if(r.error){console.error(`[I10_PROGRESS] ERROR label=${JSON.stringify(label)} elapsed_ms=${elapsed} code=${r.error.code??'UNKNOWN'}`);throw r.error;}if(r.status!==0){console.error(`[I10_PROGRESS] FAIL label=${JSON.stringify(label)} elapsed_ms=${elapsed} status=${r.status}`);throw new Error(`COMMAND_FAILED:${label}:${r.status}${opts.capture?`\n${r.stdout}\n${r.stderr}`:''}`);}console.log(`[I10_PROGRESS] PASS label=${JSON.stringify(label)} elapsed_ms=${elapsed}`);return r;}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            

Error: COMMAND_FAILED:worker:full-i10:1
    at run (file:///tmp/pb01-i10-c5/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_lib.mjs:12:1266)
    at file:///tmp/pb01-i10-c5/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_validate_current_run.mjs:9:1

Node.js v24.19.0
```

## C5 generation tail
```text
{
  "candidate": "/home/runner/work/epd2-civic-os/epd2-civic-os/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5.zip",
  "sha256": "ae62868b7f67eba6e3e2652f03167c965f32653d788d190c1f5b067e1e53bb2c",
  "file_count": 2584,
  "byte_counts": {
    "added": 3,
    "modified": 9,
    "deleted": 0,
    "archive_mode_modified": 12
  },
  "governed_executables": 12
}
```
