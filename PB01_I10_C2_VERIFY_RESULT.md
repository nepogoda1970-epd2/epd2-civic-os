# PB01-I10 C2 Final Acceptance Result

- Verdict: **FAIL**
- Workflow run: 32366109392
- Commit: 3c0777d97feeac2f6a2b01fb1746361e761944cb
- Candidate: EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2.zip
- Expected SHA-256: edbb427cb8b7651ac1c351d9f3f8b8de46945152dcea82637a45d540cbbc49c6
- validate:i10 outcome: failure

## Validation tail
```text
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
{"status":"PASS","critical_artifacts":2079,"schema_version":"epd2.pb01.accepted-lineage/2","lineage_complete":true,"historical_provenance_exception_count":1,"historical_provenance_exception_stage":"I05","evidence_bindings":5}
file:///tmp/epd2-i10-cleanroom-I5zRge/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2/scripts/i10_lib.mjs:10
export function req(c,m){if(!c)throw new Error(m);}
                                     ^

Error: HYGIENE:node_modules/.bin/playwright
    at req (file:///tmp/epd2-i10-cleanroom-I5zRge/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2/scripts/i10_lib.mjs:10:38)
    at file:///tmp/epd2-i10-cleanroom-I5zRge/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2/scripts/i10_static_release_checks.mjs:4:48

Node.js v24.19.0
file:///tmp/epd2-i10-cleanroom-I5zRge/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2/scripts/i10_lib.mjs:12
export function run(cmd,args=[],opts={}){const r=spawnSync(cmd,args,{cwd:opts.cwd??root,env:{...process.env,...opts.env},encoding:'utf8',stdio:opts.capture?'pipe':'inherit',maxBuffer:128*1024*1024});if(r.error)throw r.error;if(r.status!==0)throw new Error(`COMMAND_FAILED:${cmd} ${args.join(' ')}:${r.status}${opts.capture?`\n${r.stdout}\n${r.stderr}`:''}`);return r;}
                                                                                                                                                                                                                                                      ^

Error: COMMAND_FAILED:/opt/hostedtoolcache/node/24.19.0/x64/bin/node scripts/i10_static_release_checks.mjs:1
    at run (file:///tmp/epd2-i10-cleanroom-I5zRge/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2/scripts/i10_lib.mjs:12:247)
    at file:///tmp/epd2-i10-cleanroom-I5zRge/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2/scripts/i10_validate_worker.mjs:8:56

Node.js v24.19.0
file:///tmp/pb01-i10-c2/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2/scripts/i10_lib.mjs:10
export function req(c,m){if(!c)throw new Error(m);}
                                     ^

Error: I10_WORKER_FAILED
    at req (file:///tmp/pb01-i10-c2/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2/scripts/i10_lib.mjs:10:38)
    at file:///tmp/pb01-i10-c2/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C2/scripts/i10_validate_current_run.mjs:9:175

Node.js v24.19.0
```
