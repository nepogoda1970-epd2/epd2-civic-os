# PB01-I10 C4 Final Acceptance Result

- Verdict: **FAIL**
- Workflow run: 32373499122
- Commit: d4b0bc8185a219f038747e45a92ea65ba7256e13
- Source C2 SHA-256: edbb427cb8b7651ac1c351d9f3f8b8de46945152dcea82637a45d540cbbc49c6
- Reconstructed C3 SHA-256: a185446dd4b7f004ac7c1513c66d1916e76616dd9a4df89e1f991cab9cf06c58
- Candidate: EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4.zip
- Expected / reconstructed SHA-256: 371262b0ff94c7cb51813168fcbe08cc1544e3661254855bf6b0b715d96c4fb2
- validate:i10 outcome: failure

## Validation / progress tail
```text
  -   99,
  -   104,
  -   97,
  -   108,
  -   108,
  -   101,
  -   110,
  -   103,
  -   101,
  -   34,
  -   58,
  -   34,
  -   52,
  -   49,
  -   52,
  -   53,
  -   57,
  -   50,
  -   56,
  -   53,
  -   53,
  -   48,
  -   55,
  -   50,
  -   54,
  -   49,
  -   56,
  -   53,
  -   55,
  -   52,
  -   51,
  -   53,
  -   57,
  -   56,
  -   50,
  -   57,
  -   53,
  -   49,
  -   49,
  -   54,
  -   55,
  -   55,
  -   53,
  -   49,
  -   51,
  -   55,
  -   48,
  -   56,
  -   51,
  -   51,
  -   57,
  -   51,
  -   50,
  -   50,
  -   52,
  -   53,
  -   57,
  -   51,
  -   53,
  -   50,
  -   52,
  -   57,
  -   49,
  -   48,
  -   48,
  -   50,
  -   57,
  -   53,
  -   56,
  -   48,
  -   54,
  -   52,
  -   51,
  -   48,
  -   48,
  -   50,
  -   57,
  -   51,
  -   49,
  -   48,
  -   53,
  -   54,
  -   55,
  -   48,
  -   52,
  -   54,
  -   55,
  -   34,
  -   44,
  -   34,
  -   114,
  -   101,
  -   115,
  -   112,
  -   111,
  -   110,
  -   115,
  -   101,
  -   34,
  -   58,
  -   34,
  -   53,
  -   55,
  -   57,
  -   53,
  -   54,
  -   52,
  -   53,
  -   49,
  -   56,
  -   50,
  -   48,
  -   49,
  -   51,
  -   50,
  -   55,
  -   50,
  -   51,
  -   48,
  -   52,
  -   49,
  -   53,
  -   54,
  -   48,
  -   53,
  -   54,
  -   56,
  -   48,
  -   57,
  -   53,
  -   54,
  -   53,
  -   53,
  -   57,
  -   51,
  -   57,
  -   57,
  -   48,
  -   52,
  -   54,
  -   50,
  -   55,
  -   54,
  -   51,
  -   54,
  -   54,
  -   50,
  -   50,
  -   52,
  -   50,
  -   56,
  -   53,
  -   57,
  -   57,
  -   56,
  -   49,
  -   52,
  -   57,
  -   53,
  -   55,
  -   48,
  -   48,
  -   51,
  -   54,
  -   56,
  -   54,
  -   56,
  -   51,
  -   48,
  -   52,
  -   52,
  -   48,
  -   50,
  -   57,
  -   50,
  -   53,
  -   50,
  -   34,
  -   125,
  -   125,
  -   125
  - ]
  
      at TestContext.<anonymous> (file:///tmp/epd2-i10-cleanroom-qGrrNw/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4/tests/ledger-tamper.test.mjs:76:10)
      at async Test.run (node:internal/test_runner/test:1389:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: null,
    expected: <Buffer 7b 22 65 6c 65 63 74 69 6f 6e 5f 75 75 69 64 22 3a 22 33 4b 4d 66 50 77 39 4e 36 59 68 44 32 73 51 37 56 78 52 63 22 2c 22 65 6c 65 63 74 69 6f 6e 5f ... 2194 more bytes>,
    operator: 'deepStrictEqual',
    diff: 'simple'
  }

test at tests/security.test.mjs:18:1
✖ privacy-preserving storage and audit contain no selection, credential token or randomness (60.969101ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  
  422 !== 201
  
      at TestContext.<anonymous> (file:///tmp/epd2-i10-cleanroom-qGrrNw/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4/tests/security.test.mjs:23:10)
      at process.processTicksAndRejections (node:internal/process/task_queues:104:5)
      at async Test.run (node:internal/test_runner/test:1389:7)
      at async startSubtestAfterBootstrap (node:internal/test_runner/harness:387:3) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: 422,
    expected: 201,
    operator: 'strictEqual',
    diff: 'simple'
  }
file:///tmp/pb01-i10-c4/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4/scripts/i10_lib.mjs:12
export function run(cmd,args=[],opts={}){const cwd=opts.cwd??root;const timeoutMs=opts.timeoutMs??I10_TIMEOUTS.unit;const label=opts.label??`${cmd} ${args.join(' ')}`;const started=Date.now();console.log(`[I10_PROGRESS] START label=${JSON.stringify(label)} timeout_ms=${timeoutMs}`);const common={cwd,env:{...process.env,...opts.env},encoding:'utf8',stdio:opts.capture?'pipe':'inherit',maxBuffer:128*1024*1024};let r;if(process.platform==='linux'){const seconds=Math.max(1,Math.ceil(timeoutMs/1000));r=spawnSync('timeout',['--signal=TERM','--kill-after=10s',`${seconds}s`,cmd,...args],common);}else{r=spawnSync(cmd,args,{...common,timeout:timeoutMs,killSignal:'SIGKILL'});}const elapsed=Date.now()-started;const timedOut=(process.platform==='linux'&&r.status===124)||r.error?.code==='ETIMEDOUT';if(timedOut){console.error(`[I10_PROGRESS] TIMEOUT label=${JSON.stringify(label)} elapsed_ms=${elapsed} timeout_ms=${timeoutMs}`);throw new Error(`COMMAND_TIMEOUT:${label}:${timeoutMs}`);}if(r.error){console.error(`[I10_PROGRESS] ERROR label=${JSON.stringify(label)} elapsed_ms=${elapsed} code=${r.error.code??'UNKNOWN'}`);throw r.error;}if(r.status!==0){console.error(`[I10_PROGRESS] FAIL label=${JSON.stringify(label)} elapsed_ms=${elapsed} status=${r.status}`);throw new Error(`COMMAND_FAILED:${label}:${r.status}${opts.capture?`\n${r.stdout}\n${r.stderr}`:''}`);}console.log(`[I10_PROGRESS] PASS label=${JSON.stringify(label)} elapsed_ms=${elapsed}`);return r;}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            

Error: COMMAND_FAILED:worker:full-i10:1
    at run (file:///tmp/pb01-i10-c4/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4/scripts/i10_lib.mjs:12:1266)
    at file:///tmp/pb01-i10-c4/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4/scripts/i10_validate_current_run.mjs:9:1

Node.js v24.19.0
```

## Generation tail
```text
{
  "candidate": "/home/runner/work/epd2-civic-os/epd2-civic-os/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4.zip",
  "sha256": "371262b0ff94c7cb51813168fcbe08cc1544e3661254855bf6b0b715d96c4fb2",
  "counts": {
    "added": 3,
    "modified": 10,
    "deleted": 0
  },
  "file_count": 2581,
  "root": "/tmp/i10-c4-builder/EPD2_VCRYPTO-PB01-I10_FINAL_CRYPTOGRAPHIC_PROFILE_FREEZE_AND_RELEASE_READINESS_DECISION_CANDIDATE_0.1_C4"
}
```
