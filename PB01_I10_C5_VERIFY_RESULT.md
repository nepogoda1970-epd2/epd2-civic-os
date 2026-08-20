# PB01-I10 C5 Final Acceptance Result

- Verdict: **FAIL**
- Workflow run: 32376667695
- Commit: 4ac0332391f2078b7eab2eeffc9f5bf5121f832e
- Candidate: EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5.zip
- Expected / reconstructed SHA-256: ae62868b7f67eba6e3e2652f03167c965f32653d788d190c1f5b067e1e53bb2c
- validate:i10 outcome: failure

## Validation progress tail
```text
✔ I09/PG deterministic injected 40001 remains a retry-policy test only (311.08472ms)
✔ I09/PG retry budget exhausted produces explicit operational failure and no tally (263.081727ms)
✔ I09/PG non-retryable database SQLSTATE fails immediately (186.466043ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 879.465716
✔ I09 C1/PG burst produces 40001 from real concurrent SERIALIZABLE transactions and converges (319.679642ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 441.924457
✔ I09 C1 mixed A: tally during uncommitted finalization fails closed, retry after commit yields one canonical tally (287.410088ms)
✔ I09 C1 mixed B: publication cannot cross an uncommitted decryption boundary (1043.172727ms)
✔ I09 C1 mixed C: read-only verifier sees no bundle during publication transaction, then complete canonical bundle PASS (842.040682ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2316.221155
{"status":"C1_CONCURRENCY_AND_MIXED_PASS","postgresql_version":"postgres (PostgreSQL) 16.14 (Ubuntu 16.14-1.pgdg24.04+1)"}
[I10_PROGRESS] PASS label="i09:concurrency" elapsed_ms=13464
[I10_PROGRESS] START label="i09:crash" timeout_ms=600000

> epd2-pb01-i06-candidate@0.1.0 test:i09:crash
> bash scripts/run_i09_postgres_class.sh tests/i05-postgres-crash-restart.test.mjs tests/i06-postgres-concurrency-crash.test.mjs tests/i07-postgres-crash.test.mjs

✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (798.843764ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (592.680557ms)
✔ I06/PG concurrent final threshold shares converge to one immutable record (1019.946116ms)
✔ I06/PG same-guardian concurrent duplicate race never double-counts threshold (335.553573ms)
✔ I06/PG CRASH-01 retry deterministically converges (779.384687ms)
✔ I06/PG CRASH-02 retry deterministically converges (629.413648ms)
✔ I06/PG CRASH-03 retry deterministically converges (763.235072ms)
✔ I06/PG CRASH-04 retry deterministically converges (652.885242ms)
✔ I07/PG crash before_result_persistence leaves no incomplete FINAL and retry converges (1465.676936ms)
✔ I07/PG crash after_result_persistence_before_evidence_publication_marker leaves no incomplete FINAL and retry converges (1091.707106ms)
✔ I07/PG crash after_evidence_persistence_before_final_status_transition leaves no incomplete FINAL and retry converges (1083.966166ms)
✔ I07/PG crash immediately after FINAL commit before response preserves one final result and retry is idempotent (1078.225149ms)
ℹ tests 12
ℹ suites 0
ℹ pass 12
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 10642.108459
[I10_PROGRESS] PASS label="i09:crash" elapsed_ms=11873
[I10_PROGRESS] START label="i09:restart" timeout_ms=600000

> epd2-pb01-i06-candidate@0.1.0 test:i09:restart
> bash scripts/run_i09_postgres_class.sh tests/i05-postgres-crash-restart.test.mjs tests/i06-postgres-restart-backup.test.mjs tests/i07-postgres-restart-backup.test.mjs

✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (792.485004ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (597.570184ms)
✔ I06/PG hard database crash/restart preserves same immutable plaintext and record digest (1234.210309ms)
✔ I06/PG backup/restore preserves exact public ceremony/share/decryption evidence and no private guardian columns exist (923.020266ms)
✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (1904.933389ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1523.72103ms)
ℹ tests 6
ℹ suites 0
ℹ pass 6
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 7320.693367
[I10_PROGRESS] PASS label="i09:restart" elapsed_ms=8549
[I10_PROGRESS] START label="i09:backup-restore" timeout_ms=600000

> epd2-pb01-i06-candidate@0.1.0 test:i09:backup-restore
> bash scripts/run_i09_postgres_class.sh tests/i07-postgres-restart-backup.test.mjs

✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (1930.422592ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1542.653697ms)
ℹ tests 2
ℹ suites 0
ℹ pass 2
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3597.065201
[I10_PROGRESS] PASS label="i09:backup-restore" elapsed_ms=4841
[I10_PROGRESS] START label="i09:postgres-full" timeout_ms=1200000

> epd2-pb01-i06-candidate@0.1.0 test:i09:postgres
> I09_PG_STAGE=i03 bash scripts/run_i09_postgres_class.sh tests/postgres.integration.test.mjs tests/postgres-crash-concurrency.test.mjs tests/postgres-tamper-backup-roles.test.mjs && I09_PG_STAGE=i04 bash scripts/run_i09_postgres_class.sh tests/i04-finalization.integration.test.mjs tests/i04-concurrency-crash.test.mjs tests/i04-tamper-backup-roles.test.mjs && I09_PG_STAGE=i05 bash scripts/run_i09_postgres_class.sh tests/i05-postgres.integration.test.mjs tests/i05-postgres-runtime.test.mjs tests/i05-postgres-crash-restart.test.mjs tests/i05-postgres-tamper-backup-roles.test.mjs && I09_PG_STAGE=i06 bash scripts/run_i09_postgres_class.sh tests/i06-postgres-ceremony-decryption.test.mjs tests/i06-postgres-concurrency-crash.test.mjs tests/i06-postgres-restart-backup.test.mjs tests/i06-postgres-tamper-roles.test.mjs && I09_PG_STAGE=i07 bash scripts/run_i09_postgres_class.sh tests/i07-postgres-publication.test.mjs tests/i07-postgres-crash.test.mjs tests/i07-postgres-tamper.test.mjs tests/i07-postgres-restart-backup.test.mjs

✔ PG concurrent same key and same digest create one logical acceptance (178.079265ms)
✔ PG concurrent legitimate revotes coexist under one private lifecycle (102.309717ms)
✔ PG CRASH-01 after crypto before transaction leaves no accepted state (66.093817ms)
✔ PG CRASH-02/04 committed response loss survives service restart and retry (97.315845ms)
✔ PG CRASH-03 client disconnect cannot lose a committed acceptance (91.773572ms)
✔ PG append-only triggers and hash-chain checkpoint detect privileged tampering (204.911276ms)
✔ PG backup/restore preserves exact bytes, receipt state, ledger and private/public split (234.088709ms)
✔ PG submission runtime and evidence reader have no DDL or mutation authority (65.310916ms)
✔ PG-I03-P01 real I02 ballot follows native verification and PostgreSQL acceptance (146.251648ms)
✔ PG-I03-P02 idempotent retry returns same receipt; same key with different ballot conflicts (130.607794ms)
ℹ tests 10
ℹ suites 0
ℹ pass 10
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1617.067654
✔ I04 concurrent identical and conflicting finalizers converge without split state (199.326002ms)
✔ I04-CRASH-01 is atomic and retry converges (141.151786ms)
✔ I04-CRASH-02 is atomic and retry converges (130.635433ms)
✔ I04-CRASH-03 is atomic and retry converges (129.913982ms)
✔ I04-CRASH-04 is atomic and retry converges (126.417712ms)
✔ I04 submission-versus-closure race has one deterministic boundary outcome (143.454349ms)
✔ I04 real I03 revote E2E selects latest valid, preserves history and exact bytes (236.143124ms)
✔ I04 multi-lifecycle resolution yields A2, B1 and C3 in I01 digest order (256.881789ms)
✔ I04 empty election finalizes deterministically (100.990231ms)
✔ I04 public verifier detects every committed-field tamper class (235.649516ms)
✔ I04 refuses finalization when I03 ledger integrity has been altered (126.615985ms)
✔ I04 PostgreSQL roles enforce submission/finalizer/evidence/migration separation (180.133794ms)
✔ I04 backup/restore preserves exact I03 history and identical final artifacts (394.260683ms)
ℹ tests 13
ℹ suites 0
ℹ pass 13
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2726.20924
✔ I05/PG CRASH-01..04 leave no partial tally state and every retry converges on one identical tally (808.20456ms)
✔ I05/PG committed tally survives an immediate-mode server crash and restart with identical bytes and digests (592.244773ms)
✔ I05/PG exact finalized I04 set becomes the tally input and native Belenios re-verification runs per ballot (289.747187ms)
✔ I05/PG idempotent retry replays one physical tally without recomputing a second record (268.112606ms)
✔ I05/PG concurrent tally executions never diverge and every caller converges on one identical tally (202.543176ms)
✔ I05/PG rejects a conflicting F_final and a conflicting tally record against the same election (253.77401ms)
✔ I05/PG recompute reproduces the committed tally byte-for-byte from PostgreSQL state (265.327985ms)
✔ I05/PG append-only triggers reject mutation of committed tally state even for the schema owner (303.998746ms)
✔ I05/PG privileged tamper that bypasses the triggers is still detected by evidence and recompute (281.819366ms)
✔ I05/PG tally runtime cannot mutate I03 or I04 state (207.18485ms)
✔ I05/PG submission, finalizer and evidence roles cannot mutate I05 tally state (237.20436ms)
✔ I05/PG tally and evidence roles hold no DDL or TEMP privilege anywhere (201.68964ms)
✔ I05/PG backup and restore preserve exact aggregate and tally bytes and every digest (453.405199ms)
✔ I05 PostgreSQL exact finalized set tally, idempotency, recompute, concurrency and privileges (358.099861ms)
✔ I05 PostgreSQL CRASH-03 rolls aggregate insert back; retry converges (234.304536ms)
ℹ tests 15
ℹ suites 0
ℹ pass 15
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 5410.298634
✔ I06/PG real threshold ceremony freezes immutable N=3 T=2 public context (598.102891ms)
✔ I06/PG T-1 exposes no plaintext; exact threshold commits one immutable result; extra valid share cannot change plaintext (862.393071ms)
✔ I06/PG duplicate guardian and malformed/invalid share fail closed (517.228512ms)
✔ I06/PG concurrent final threshold shares converge to one immutable record (1032.110975ms)
✔ I06/PG same-guardian concurrent duplicate race never double-counts threshold (349.233919ms)
✔ I06/PG CRASH-01 retry deterministically converges (785.79672ms)
✔ I06/PG CRASH-02 retry deterministically converges (631.763829ms)
✔ I06/PG CRASH-03 retry deterministically converges (768.015989ms)
✔ I06/PG CRASH-04 retry deterministically converges (654.681497ms)
✔ I06/PG hard database crash/restart preserves same immutable plaintext and record digest (1336.47786ms)
✔ I06/PG backup/restore preserves exact public ceremony/share/decryption evidence and no private guardian columns exist (910.514219ms)
✔ I06/PG mandatory I05 corrective detects privileged aggregate-byte-only rewrite and decryption refuses (1009.447969ms)
✔ I06/PG privileged tamper: guardian public key after freeze is detected (512.080609ms)
✔ I06/PG privileged tamper: threshold after ceremony freeze is detected (494.7677ms)
✔ I06/PG privileged tamper: frozen guardian-set member replacement is detected (488.777581ms)
✔ I06/PG privileged tamper: partial-decryption factor bytes are detected (513.253946ms)
✔ I06/PG privileged tamper: partial-decryption proof bytes are detected (516.587781ms)
✔ I06/PG privileged tamper: accepted share digest column is detected (522.609119ms)
✔ I06/PG privileged tamper: aggregate digest alone is detected (499.851351ms)
✔ I06/PG privileged tamper: final plaintext bytes are detected (516.279371ms)
✔ I06/PG privileged tamper: final decryption-record digest is detected (515.391713ms)
✔ I06/PG roles enforce coordinator/ingester/finalizer/runtime separation (509.819648ms)
ℹ tests 22
ℹ suites 0
ℹ pass 22
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 15024.720655
✔ I07/PG crash before_result_persistence leaves no incomplete FINAL and retry converges (1481.896747ms)
✔ I07/PG crash after_result_persistence_before_evidence_publication_marker leaves no incomplete FINAL and retry converges (1101.878316ms)
✔ I07/PG crash after_evidence_persistence_before_final_status_transition leaves no incomplete FINAL and retry converges (1089.103866ms)
✔ I07/PG crash immediately after FINAL commit before response preserves one final result and retry is idempotent (1088.857018ms)
✔ I07/PG real persistence path publishes one final bundle independently verified by A and B (1695.972685ms)
✔ I07/PG concurrent publishers converge to one immutable canonical result (954.893327ms)
✔ I07/PG idempotent retry returns same result and conflicting direct commit is rejected (901.224937ms)
✔ I07/PG least privilege: publisher has only scoped I07 write + I06 authority read; public verifier is read-only FINAL view (720.800751ms)
✔ I07/PG hard stop/restart preserves exact final public evidence and independent A/B verification (2020.982658ms)
✔ I07/PG backup/restore preserves byte-identical canonical bundle and independent A/B PASS (1528.01111ms)
✔ I07/PG privileged tamper aggregate bytes is detected independently of DB permissions (1081.778417ms)
✔ I07/PG privileged tamper guardian public key is detected independently of DB permissions (746.381511ms)
✔ I07/PG privileged tamper threshold is detected independently of DB permissions (722.389791ms)
✔ I07/PG privileged tamper accepted share artifact is detected independently of DB permissions (733.884102ms)
✔ I07/PG privileged tamper accepted share digest is detected independently of DB permissions (749.262085ms)
✔ I07/PG privileged tamper plaintext bytes is detected independently of DB permissions (738.722424ms)
✔ I07/PG privileged tamper plaintext digest is detected independently of DB permissions (740.229711ms)
✔ I07/PG privileged tamper decryption record canonical is detected independently of DB permissions (741.661783ms)
✔ I07/PG privileged tamper public result canonical bytes is detected independently of DB permissions (890.836582ms)
✔ I07/PG privileged tamper public result digest column is detected independently of DB permissions (894.729655ms)
ℹ tests 20
ℹ suites 0
ℹ pass 20
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 21111.844874
[I10_PROGRESS] PASS label="i09:postgres-full" elapsed_ms=51136
[I10_PROGRESS] START label="i09:scale-100-1000-10000" timeout_ms=900000

> epd2-pb01-i06-candidate@0.1.0 test:i09:scale
> node scripts/i09_scale_worker.mjs 100 && node scripts/i09_scale_worker.mjs 1000 && node scripts/i09_scale_worker.mjs 10000

I09_SCALE_PROGRESS:I09-S100:setup
I09_SCALE_PROGRESS:I09-S100:ballots:1157
I09_SCALE_PROGRESS:I09-S100:finalset:16
I09_SCALE_PROGRESS:I09-S100:tally:366
I09_SCALE_PROGRESS:I09-S100:decrypt:674
I09_SCALE_PROGRESS:I09-S100:evidence:8
file:///tmp/epd2-i10-cleanroom-w4xB5Z/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i09_scale_worker.mjs:39
 const goOutRel=`evidence/results/i09/scale/${fixtureId}/go.json`,goOut=join(root,goOutRel);await run('go',['run','verifier/reference-go-i07/main.go','--root','.', '--tool',tool,'--bundle',bundlePath,'--trust',trustPath,'--out',goOutRel],{cwd:root,timeout:1200000});const goReport=JSON.parse(await readFile(goOut,'utf8'));const rustBin=process.env.I08_RUST_BIN;if(!rustBin)throw new Error('I09_FRESH_RUST_REQUIRED');if(process.env.I08_RUST_EXECUTABLE_CLASS!=='fresh_build')throw new Error('I09_FRESH_RUST_CLASS_REQUIRED');const rustOut=join(outDir,'rust.json');const rustStart=performance.now();await run(rustBin,['--root','.', '--mode','single','--bundle',bundlePath,'--trust',trustPath,'--out',rustOut],{cwd:root,timeout:1200000});const rustMs=performance.now()-rustStart;const rustReport=JSON.parse(await readFile(rustOut,'utf8'));const goRes=goReport.vector_results?.[0]??goReport;const rustRes=rustReport.vector_results?.[0]??rustReport;const fields=['status','election_digest','final_set_reference','aggregate_digest','ceremony_digest','share_digests','plaintext_tally_digest','decryption_record_digest','public_result_digest','public_evidence_bundle_digest'];const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);const agree=fields.every(k=>same(nres[k],goRes[k])&&same(nres[k],rustRes[k]));if(!agree)throw new Error('I09_SCALE_CROSS_LANGUAGE_DIVERGENCE');const result={schema_version:'epd2.pb01.i09-scale-result/1',fixture_id:fixtureId,raw_submissions:rows.length,effective_final_set_size:size,revote_count:revotes,timings_ms:{setup_and_credentials:Math.round(ballotStart-t0),ballot_validation_and_generation:Math.round(ballotValidationMs),final_set_derivation:Math.round(finalSetMs),tally_computation:Math.round(tallyMs),decryption_verification:Math.round(decryptionMs),result_evidence_generation:Math.round(evidenceMs),independent_rust_verification:Math.round(rustMs)},result_digest:publicResult.public_result_digest,aggregate_digest:tallyArtifacts.homomorphicTallyRecord.aggregate_ciphertext_digest,plaintext_tally:record.plaintext_tally,verifier_result:{node:nres.status,go:goRes.status,rust:rustRes.status,byte_for_byte_agreement:agree},resource_observations:{peak_memory:'measured externally where runner supports /usr/bin/time; no SLA claim'},status:'PASS'};await writeFile(join(outDir,'scale-result.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));await rm(dec,{recursive:true,force:true});
                                                                                                                                                                                                                                                                                                                                                                                           ^

Error: I09_FRESH_RUST_REQUIRED
    at file:///tmp/epd2-i10-cleanroom-w4xB5Z/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i09_scale_worker.mjs:39:380

Node.js v24.19.0
[I10_PROGRESS] FAIL label="i09:scale-100-1000-10000" elapsed_ms=4491 status=1
file:///tmp/epd2-i10-cleanroom-w4xB5Z/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_lib.mjs:12
export function run(cmd,args=[],opts={}){const cwd=opts.cwd??root;const timeoutMs=opts.timeoutMs??I10_TIMEOUTS.unit;const label=opts.label??`${cmd} ${args.join(' ')}`;const started=Date.now();console.log(`[I10_PROGRESS] START label=${JSON.stringify(label)} timeout_ms=${timeoutMs}`);const common={cwd,env:{...process.env,...opts.env},encoding:'utf8',stdio:opts.capture?'pipe':'inherit',maxBuffer:128*1024*1024};let r;if(process.platform==='linux'){const seconds=Math.max(1,Math.ceil(timeoutMs/1000));r=spawnSync('timeout',['--signal=TERM','--kill-after=10s',`${seconds}s`,cmd,...args],common);}else{r=spawnSync(cmd,args,{...common,timeout:timeoutMs,killSignal:'SIGKILL'});}const elapsed=Date.now()-started;const timedOut=(process.platform==='linux'&&r.status===124)||r.error?.code==='ETIMEDOUT';if(timedOut){console.error(`[I10_PROGRESS] TIMEOUT label=${JSON.stringify(label)} elapsed_ms=${elapsed} timeout_ms=${timeoutMs}`);throw new Error(`COMMAND_TIMEOUT:${label}:${timeoutMs}`);}if(r.error){console.error(`[I10_PROGRESS] ERROR label=${JSON.stringify(label)} elapsed_ms=${elapsed} code=${r.error.code??'UNKNOWN'}`);throw r.error;}if(r.status!==0){console.error(`[I10_PROGRESS] FAIL label=${JSON.stringify(label)} elapsed_ms=${elapsed} status=${r.status}`);throw new Error(`COMMAND_FAILED:${label}:${r.status}${opts.capture?`\n${r.stdout}\n${r.stderr}`:''}`);}console.log(`[I10_PROGRESS] PASS label=${JSON.stringify(label)} elapsed_ms=${elapsed}`);return r;}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            

Error: COMMAND_FAILED:i09:scale-100-1000-10000:1
    at run (file:///tmp/epd2-i10-cleanroom-w4xB5Z/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_lib.mjs:12:1266)
    at file:///tmp/epd2-i10-cleanroom-w4xB5Z/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C5/scripts/i10_validate_worker.mjs:29:4

Node.js v24.19.0
[I10_PROGRESS] FAIL label="worker:full-i10" elapsed_ms=129261 status=1
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
