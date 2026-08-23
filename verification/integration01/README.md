# INTEGRATION-01 C1 authoritative acceptance

Temporary verification branch only. **DO NOT MERGE.**

Required materialized baseline:

`accepted PILOT-04 C9 + accepted DATA-04 C1 + frozen PB01 C6 -> INTEGRATION-01 C1`

The accepted DATA-04 C1 is cumulative over accepted DATA-03/DATA-02/DATA-01 semantics; DATA-03 is therefore not a separate integration input here.

Acceptance is exact-byte and fail-closed. The target candidate remains `READY_FOR_INDEPENDENT_GITHUB_ACCEPTANCE` until a fresh canonical GitHub run passes all mandatory gates and the uploaded exact candidate artifact is independently re-downloaded and SHA-256 verified.

Required canonical classes include exact input identities, package/manifest preflight, Python/Node/npm/uv/PostgreSQL versions, frozen dependency installation, Ruff lint/format, typecheck, DATA-04 live + inherited DATA regression, PILOT-04 mandatory security properties, full pytest regression, browser regression, actual frozen PB01 integrity, cross-boundary integration assertions, fresh evidence digest, and exact candidate artifact identity.

Any runner/harness failure must be separated from a candidate defect. Temporary verification files are not part of the governed candidate identity.
