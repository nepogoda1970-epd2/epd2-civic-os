# PB01-I09 C2 Independent External Acceptance v3

- Workflow run: 32296994399
- Source commit: 085de5d5b05c6b48e310a00be37c45f93ecaa3ba
- Candidate SHA256: `48fbddb686466208e4972908a3c213aa7021f4178d8bf71cc0b211f4af45ba53`
- Node: `v24.19.0`
- Go: `go version go1.23.2 linux/amd64`
- Rust: `rustc 1.97.1 (8bab26f4f 2026-07-14)`
- Cargo: `cargo 1.97.1 (c980f4866 2026-06-30)`
- PostgreSQL: `/usr/lib/postgresql/16/bin/postgres --version`
- Fresh validate:i09 result: `NO PASS RESULT`

**Verdict: NOT VERIFIED — external run did not produce the mandatory fresh PASS result.**

## Log tail
```text

> epd2-pb01-i06-candidate@0.1.0 validate:i09
> node scripts/i09_validate_current_run.mjs

go version go1.23.2 linux/amd64
rustc 1.97.1 (8bab26f4f 2026-07-14)
cargo 1.97.1 (c980f4866 2026-06-30)
postgres (PostgreSQL) 16.14 (Ubuntu 16.14-1.pgdg24.04+1)
{
  "status": "FAIL",
  "undeclared_predecessor_mismatches": [
    {
      "path": "tests/i05_postgres_helpers.mjs",
      "type": "changed"
    }
  ]
}
file:///tmp/pb01-i09-c2-v3/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/scripts/i09_validate_current_run.mjs:28
      : rejectRun(Object.assign(new Error(`${cmd} ${args.join(' ')} exit ${code}: ${Buffer.concat(err).toString().slice(-4000)}`), { exitCode: code })));
                                ^

Error: /opt/hostedtoolcache/node/24.19.0/x64/bin/node scripts/i09_check_predecessor.mjs exit 1: {
  "status": "FAIL",
  "undeclared_predecessor_mismatches": [
    {
      "path": "tests/i05_postgres_helpers.mjs",
      "type": "changed"
    }
  ]
}

    at ChildProcess.<anonymous> (file:///tmp/pb01-i09-c2-v3/EPD2_VCRYPTO-PB01-I09_PRODUCTION_PILOT_ROBUSTNESS_CONCURRENCY_AND_SCALE_QUALIFICATION_CANDIDATE_0.1_C2/scripts/i09_validate_current_run.mjs:28:33)
    at ChildProcess.emit (node:events:509:28)
    at ChildProcess._handle.onexit (node:internal/child_process:295:12) {
  exitCode: 1
}

Node.js v24.19.0
```
