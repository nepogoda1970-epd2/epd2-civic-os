# PB01-I10 C5 Final Acceptance Result

- Verdict: **FAIL**
- Workflow run: 32376023167
- Commit: e92e923399868fd109053da5e6d3d82decb83b29
- Candidate: EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5.zip
- Expected / reconstructed SHA-256: ae62868b7f67eba6e3e2652f03167c965f32653d788d190c1f5b067e1e53bb2c
- validate:i10 outcome: failure

## Validation progress tail
```text
./verifier/rust/vendor/syn/src/scan_expr.rs: OK
./verifier/rust/vendor/syn/src/sealed.rs: OK
./verifier/rust/vendor/syn/src/span.rs: OK
./verifier/rust/vendor/syn/src/spanned.rs: OK
./verifier/rust/vendor/syn/src/stmt.rs: OK
./verifier/rust/vendor/syn/src/thread.rs: OK
./verifier/rust/vendor/syn/src/token.rs: OK
./verifier/rust/vendor/syn/src/tt.rs: OK
./verifier/rust/vendor/syn/src/ty.rs: OK
./verifier/rust/vendor/syn/src/verbatim.rs: OK
./verifier/rust/vendor/syn/src/whitespace.rs: OK
./verifier/rust/vendor/syn/tests/common/eq.rs: OK
./verifier/rust/vendor/syn/tests/common/mod.rs: OK
./verifier/rust/vendor/syn/tests/common/parse.rs: OK
./verifier/rust/vendor/syn/tests/common/visit.rs: OK
./verifier/rust/vendor/syn/tests/debug/gen.rs: OK
./verifier/rust/vendor/syn/tests/debug/mod.rs: OK
./verifier/rust/vendor/syn/tests/macros/mod.rs: OK
./verifier/rust/vendor/syn/tests/regression.rs: OK
./verifier/rust/vendor/syn/tests/regression/issue1108.rs: OK
./verifier/rust/vendor/syn/tests/regression/issue1235.rs: OK
./verifier/rust/vendor/syn/tests/repo/mod.rs: OK
./verifier/rust/vendor/syn/tests/repo/progress.rs: OK
./verifier/rust/vendor/syn/tests/snapshot/mod.rs: OK
./verifier/rust/vendor/syn/tests/test_attribute.rs: OK
./verifier/rust/vendor/syn/tests/test_derive_input.rs: OK
./verifier/rust/vendor/syn/tests/test_expr.rs: OK
./verifier/rust/vendor/syn/tests/test_generics.rs: OK
./verifier/rust/vendor/syn/tests/test_grouping.rs: OK
./verifier/rust/vendor/syn/tests/test_ident.rs: OK
./verifier/rust/vendor/syn/tests/test_item.rs: OK
./verifier/rust/vendor/syn/tests/test_lit.rs: OK
./verifier/rust/vendor/syn/tests/test_meta.rs: OK
./verifier/rust/vendor/syn/tests/test_parse_buffer.rs: OK
./verifier/rust/vendor/syn/tests/test_parse_quote.rs: OK
./verifier/rust/vendor/syn/tests/test_parse_stream.rs: OK
./verifier/rust/vendor/syn/tests/test_pat.rs: OK
./verifier/rust/vendor/syn/tests/test_path.rs: OK
./verifier/rust/vendor/syn/tests/test_precedence.rs: OK
./verifier/rust/vendor/syn/tests/test_punctuated.rs: OK
./verifier/rust/vendor/syn/tests/test_receiver.rs: OK
./verifier/rust/vendor/syn/tests/test_round_trip.rs: OK
./verifier/rust/vendor/syn/tests/test_shebang.rs: OK
./verifier/rust/vendor/syn/tests/test_size.rs: OK
./verifier/rust/vendor/syn/tests/test_stmt.rs: OK
./verifier/rust/vendor/syn/tests/test_token_trees.rs: OK
./verifier/rust/vendor/syn/tests/test_ty.rs: OK
./verifier/rust/vendor/syn/tests/test_unparenthesize.rs: OK
./verifier/rust/vendor/syn/tests/test_visibility.rs: OK
./verifier/rust/vendor/syn/tests/zzz_stable.rs: OK
./verifier/rust/vendor/typenum/.cargo-checksum.json: OK
./verifier/rust/vendor/typenum/.cargo_vcs_info.json: OK
./verifier/rust/vendor/typenum/CHANGELOG.md: OK
./verifier/rust/vendor/typenum/Cargo.lock: OK
./verifier/rust/vendor/typenum/Cargo.toml: OK
./verifier/rust/vendor/typenum/Cargo.toml.orig: OK
./verifier/rust/vendor/typenum/LICENSE: OK
./verifier/rust/vendor/typenum/LICENSE-APACHE: OK
./verifier/rust/vendor/typenum/LICENSE-MIT: OK
./verifier/rust/vendor/typenum/README.md: OK
./verifier/rust/vendor/typenum/src/array.rs: OK
./verifier/rust/vendor/typenum/src/bit.rs: OK
./verifier/rust/vendor/typenum/src/gen.rs: OK
./verifier/rust/vendor/typenum/src/gen/consts.rs: OK
./verifier/rust/vendor/typenum/src/gen/generic_const_mappings.rs: OK
./verifier/rust/vendor/typenum/src/gen/op.rs: OK
./verifier/rust/vendor/typenum/src/int.rs: OK
./verifier/rust/vendor/typenum/src/lib.rs: OK
./verifier/rust/vendor/typenum/src/marker_traits.rs: OK
./verifier/rust/vendor/typenum/src/operator_aliases.rs: OK
./verifier/rust/vendor/typenum/src/private.rs: OK
./verifier/rust/vendor/typenum/src/tuple.rs: OK
./verifier/rust/vendor/typenum/src/type_operators.rs: OK
./verifier/rust/vendor/typenum/src/uint.rs: OK
./verifier/rust/vendor/typenum/tests/generated.rs: OK
./verifier/rust/vendor/unicode-ident/.cargo-checksum.json: OK
./verifier/rust/vendor/unicode-ident/.cargo_vcs_info.json: OK
./verifier/rust/vendor/unicode-ident/.github/FUNDING.yml: OK
./verifier/rust/vendor/unicode-ident/.github/workflows/ci.yml: OK
./verifier/rust/vendor/unicode-ident/Cargo.lock: OK
./verifier/rust/vendor/unicode-ident/Cargo.toml: OK
./verifier/rust/vendor/unicode-ident/Cargo.toml.orig: OK
./verifier/rust/vendor/unicode-ident/LICENSE-APACHE: OK
./verifier/rust/vendor/unicode-ident/LICENSE-MIT: OK
./verifier/rust/vendor/unicode-ident/LICENSE-UNICODE: OK
./verifier/rust/vendor/unicode-ident/README.md: OK
./verifier/rust/vendor/unicode-ident/benches/xid.rs: OK
./verifier/rust/vendor/unicode-ident/src/lib.rs: OK
./verifier/rust/vendor/unicode-ident/src/tables.rs: OK
./verifier/rust/vendor/unicode-ident/tests/compare.rs: OK
./verifier/rust/vendor/unicode-ident/tests/fst/mod.rs: OK
./verifier/rust/vendor/unicode-ident/tests/fst/xid_continue.fst: OK
./verifier/rust/vendor/unicode-ident/tests/fst/xid_start.fst: OK
./verifier/rust/vendor/unicode-ident/tests/roaring/mod.rs: OK
./verifier/rust/vendor/unicode-ident/tests/static_size.rs: OK
./verifier/rust/vendor/unicode-ident/tests/tables/mod.rs: OK
./verifier/rust/vendor/unicode-ident/tests/tables/tables.rs: OK
./verifier/rust/vendor/unicode-ident/tests/trie/mod.rs: OK
./verifier/rust/vendor/unicode-ident/tests/trie/trie.rs: OK
./verifier/rust/vendor/version_check/.cargo-checksum.json: OK
./verifier/rust/vendor/version_check/.cargo_vcs_info.json: OK
./verifier/rust/vendor/version_check/.github/workflows/ci.yml: OK
./verifier/rust/vendor/version_check/.travis.yml: OK
./verifier/rust/vendor/version_check/Cargo.toml: OK
./verifier/rust/vendor/version_check/Cargo.toml.orig: OK
./verifier/rust/vendor/version_check/LICENSE-APACHE: OK
./verifier/rust/vendor/version_check/LICENSE-MIT: OK
./verifier/rust/vendor/version_check/README.md: OK
./verifier/rust/vendor/version_check/src/channel.rs: OK
./verifier/rust/vendor/version_check/src/date.rs: OK
./verifier/rust/vendor/version_check/src/lib.rs: OK
./verifier/rust/vendor/version_check/src/version.rs: OK
./verifier/rust/vendor/wasi/.cargo-checksum.json: OK
./verifier/rust/vendor/wasi/.cargo_vcs_info.json: OK
./verifier/rust/vendor/wasi/.github/workflows/main.yml: OK
./verifier/rust/vendor/wasi/.gitmodules: OK
./verifier/rust/vendor/wasi/CODE_OF_CONDUCT.md: OK
./verifier/rust/vendor/wasi/CONTRIBUTING.md: OK
./verifier/rust/vendor/wasi/Cargo.lock: OK
./verifier/rust/vendor/wasi/Cargo.toml: OK
./verifier/rust/vendor/wasi/Cargo.toml.orig: OK
./verifier/rust/vendor/wasi/LICENSE-APACHE: OK
./verifier/rust/vendor/wasi/LICENSE-Apache-2.0_WITH_LLVM-exception: OK
./verifier/rust/vendor/wasi/LICENSE-MIT: OK
./verifier/rust/vendor/wasi/ORG_CODE_OF_CONDUCT.md: OK
./verifier/rust/vendor/wasi/README.md: OK
./verifier/rust/vendor/wasi/SECURITY.md: OK
./verifier/rust/vendor/wasi/src/lib.rs: OK
./verifier/rust/vendor/wasi/src/lib_generated.rs: OK
./verifier/rust/vendor/zeroize/.cargo-checksum.json: OK
./verifier/rust/vendor/zeroize/.cargo_vcs_info.json: OK
./verifier/rust/vendor/zeroize/CHANGELOG.md: OK
./verifier/rust/vendor/zeroize/Cargo.lock: OK
./verifier/rust/vendor/zeroize/Cargo.toml: OK
./verifier/rust/vendor/zeroize/Cargo.toml.orig: OK
./verifier/rust/vendor/zeroize/LICENSE-APACHE: OK
./verifier/rust/vendor/zeroize/LICENSE-MIT: OK
./verifier/rust/vendor/zeroize/README.md: OK
./verifier/rust/vendor/zeroize/src/aarch64.rs: OK
./verifier/rust/vendor/zeroize/src/barrier.rs: OK
./verifier/rust/vendor/zeroize/src/lib.rs: OK
./verifier/rust/vendor/zeroize/src/stack.rs: OK
./verifier/rust/vendor/zeroize/src/x86.rs: OK
./verifier/rust/vendor/zeroize/tests/alloc.rs: OK
./verifier/rust/vendor/zeroize/tests/zeroize.rs: OK
./verifier/rust/vendor/zeroize/tests/zeroize_derive.rs: OK
./verifier/verify-i04-evidence.mjs: OK
[I10_PROGRESS] PASS label="sha256sums" elapsed_ms=151
[I10_PROGRESS] START label="check:i10:freeze" timeout_ms=120000
{"status":"PASS","critical_artifacts":2079,"schema_version":"epd2.pb01.accepted-lineage/2","lineage_complete":true,"historical_provenance_exception_count":1,"historical_provenance_exception_stage":"I05","evidence_bindings":5}
[I10_PROGRESS] PASS label="check:i10:freeze" elapsed_ms=367
[I10_PROGRESS] START label="test:i10" timeout_ms=120000

> epd2-pb01-i06-candidate@0.1.0 test:i10
> node --test --test-concurrency=1 tests/i10-freeze-release.test.mjs

✔ I10 binds exact I09 C4 predecessor (7.613041ms)
✔ freeze preserves NON_BINDING_PILOT and no prebuilt authority (2.483672ms)
✔ Rust accepted source and Cargo.lock are frozen (2.761228ms)
✔ negative corpus remains 26 required rejects (0.706308ms)
✔ retry release behavior remains exact (6.892547ms)
✔ static release decision awaits independent exact ZIP validation (0.622531ms)
✔ accepted-lineage v2 closes with exactly one explicit I05 exception (1.448856ms)
✔ second historical exception fails closed (1.526494ms)
✔ exception on any stage other than I05 fails closed (1.174284ms)
✔ rejected I05 0.1 SHA substitution fails closed (1.195369ms)
✔ any fabricated non-null I05 archive SHA fails closed (1.588938ms)
✔ missing rejected I05 SHA blacklist fails closed (0.85176ms)
✔ accepted I09 C4 predecessor drift fails closed (1.287281ms)
✔ I05 downstream governed evidence bindings are live and byte-bound (2.442436ms)
✔ tampered downstream evidence binding hash fails closed (1.005048ms)
✔ full governed lineage validator passes current I10 metadata (4.23244ms)
✔ I10 validator source contains mandatory exact environment and live classes (1.507011ms)
✔ I10 archive scope and static hygiene checks run before dependency installation and are not repeated after node_modules exists (0.9043ms)
✔ I10 validation commands are bounded fail-closed and expose progress markers (0.947675ms)
✔ sealed candidate preserves governed executable file modes (1.086435ms)
ℹ tests 20
ℹ suites 0
ℹ pass 20
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 107.748786
[I10_PROGRESS] PASS label="test:i10" elapsed_ms=244
[I10_PROGRESS] START label="regression:i03-core" timeout_ms=300000

> epd2-pb01-i06-candidate@0.1.0 test
> node --test tests/unit.test.mjs tests/api.integration.test.mjs tests/concurrency-crash.test.mjs tests/ledger-tamper.test.mjs tests/security.test.mjs

✔ I03-P01..P10 real I02 ballot acceptance path (1644.402103ms)
▶ I03-N01..N10 schema, context, proof, digest, credential and size failures
  ✔ N01 unknown schema (11.510634ms)
  ✔ N02 unknown profile (7.437724ms)
  ✔ N06 wrong digest (5.617696ms)
  ✔ N04 mutated ciphertext (22.64526ms)
  ✔ N05 mutated proof challenge (16.965472ms)
  ✔ N05 mutated proof (20.728416ms)
  ✔ N05 mutated signature proof (16.314731ms)
  ✔ N01 unexpected field (4.122487ms)
  ✔ N03 foreign election (2.987323ms)
  ✔ N07 invalid credential (19.280202ms)
  ✔ N08 expired credential (19.187825ms)
  ✔ N10 oversized request rejected before crypto (7.890746ms)
  ✔ duplicate JSON member rejected (9.848641ms)
✔ I03-N01..N10 schema, context, proof, digest, credential and size failures (364.138517ms)
✔ I03-N09 and N11..N15 conflict, duplicate, storage, immutability and enumeration (107.633038ms)
✔ I03-N12 storage failure returns stable taxonomy and stores nothing (36.518993ms)
✔ concurrent same idempotency key and raw digest create one logical acceptance (1544.700128ms)
✔ different valid revotes concurrently coexist under one private lifecycle (330.470967ms)
✔ CRASH-01 after crypto before transaction leaves no accepted state (42.593944ms)
✔ CRASH-02 after commit before response and CRASH-04 restart retry recover same receipt (81.625833ms)
✔ CRASH-03 client disconnect after request body does not lose committed ballot (80.996402ms)
✔ ledger detects modification, deletion, reordering and conflicting checkpoint (1845.946547ms)
✔ backup/restore preserves exact ballot bytes, ledger and private/public separation (70.638215ms)
✔ privacy-preserving storage and audit contain no selection, credential token or randomness (107.771651ms)
✔ CORS is exact, non-credentialed and arbitrary origin is rejected (36.74563ms)
✔ cheap invalid schema is rejected before native verification (22.863839ms)
✔ bounded limiter resets and cannot permanently lock out a legitimate client (0.91776ms)
✔ I03 submission authority exposes no crypto-finalization routes; I05 tally boundary remains separately authorized (7.316961ms)
✔ submission capability grants no election administration or ledger mutation authority (32.051831ms)
✔ strict parser accepts canonical JSON and rejects duplicate members (8.335137ms)
✔ ledger domain is deterministic and commits order/link fields (1.860702ms)
✔ scoped capability is election-bound, expiring and yields opaque lifecycle handle (2.214316ms)
✔ receipt uses independent Ed25519 key and verifies (3.40824ms)
ℹ tests 34
ℹ suites 0
ℹ pass 34
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2349.108517
[I10_PROGRESS] PASS label="regression:i03-core" elapsed_ms=2492
[I10_PROGRESS] START label="regression:i04" timeout_ms=300000

> epd2-pb01-i06-candidate@0.1.0 test:i04
> I09_PG_STAGE=i04 bash scripts/run_i09_postgres_class.sh tests/i04-policy.unit.test.mjs tests/i04-finalization.integration.test.mjs tests/i04-concurrency-crash.test.mjs tests/i04-tamper-backup-roles.test.mjs

I09_ENV_POSTGRESQL_16_MISSING
[I10_PROGRESS] FAIL label="regression:i04" elapsed_ms=107 status=22
file:///tmp/epd2-i10-cleanroom-AngmeO/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_lib.mjs:12
export function run(cmd,args=[],opts={}){const cwd=opts.cwd??root;const timeoutMs=opts.timeoutMs??I10_TIMEOUTS.unit;const label=opts.label??`${cmd} ${args.join(' ')}`;const started=Date.now();console.log(`[I10_PROGRESS] START label=${JSON.stringify(label)} timeout_ms=${timeoutMs}`);const common={cwd,env:{...process.env,...opts.env},encoding:'utf8',stdio:opts.capture?'pipe':'inherit',maxBuffer:128*1024*1024};let r;if(process.platform==='linux'){const seconds=Math.max(1,Math.ceil(timeoutMs/1000));r=spawnSync('timeout',['--signal=TERM','--kill-after=10s',`${seconds}s`,cmd,...args],common);}else{r=spawnSync(cmd,args,{...common,timeout:timeoutMs,killSignal:'SIGKILL'});}const elapsed=Date.now()-started;const timedOut=(process.platform==='linux'&&r.status===124)||r.error?.code==='ETIMEDOUT';if(timedOut){console.error(`[I10_PROGRESS] TIMEOUT label=${JSON.stringify(label)} elapsed_ms=${elapsed} timeout_ms=${timeoutMs}`);throw new Error(`COMMAND_TIMEOUT:${label}:${timeoutMs}`);}if(r.error){console.error(`[I10_PROGRESS] ERROR label=${JSON.stringify(label)} elapsed_ms=${elapsed} code=${r.error.code??'UNKNOWN'}`);throw r.error;}if(r.status!==0){console.error(`[I10_PROGRESS] FAIL label=${JSON.stringify(label)} elapsed_ms=${elapsed} status=${r.status}`);throw new Error(`COMMAND_FAILED:${label}:${r.status}${opts.capture?`\n${r.stdout}\n${r.stderr}`:''}`);}console.log(`[I10_PROGRESS] PASS label=${JSON.stringify(label)} elapsed_ms=${elapsed}`);return r;}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            

Error: COMMAND_FAILED:regression:i04:22
    at run (file:///tmp/epd2-i10-cleanroom-AngmeO/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_lib.mjs:12:1266)
    at file:///tmp/epd2-i10-cleanroom-AngmeO/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_validate_worker.mjs:29:4

Node.js v24.19.0
[I10_PROGRESS] FAIL label="worker:full-i10" elapsed_ms=3437 status=1
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
