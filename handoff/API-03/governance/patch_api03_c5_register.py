from pathlib import Path
import json

p = Path('docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md')
s = p.read_text(encoding='utf-8')


def once(old: str, new: str, label: str) -> None:
    global s
    n = s.count(old)
    if n != 1:
        raise AssertionError(f'{label}: expected one occurrence, got {n}')
    s = s.replace(old, new, 1)


once(
    '| API | `API-01 ACCEPTED / CLOSED; API-02 ACCEPTED / CLOSED; API-03 ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` | API-03 is the active primary API stage. It must reconcile/rebase to exact accepted API-02 C13 bytes before seal and independent acceptance. API remains open through API-06. |',
    '| API | `API-01 ACCEPTED / CLOSED; API-02 ACCEPTED / CLOSED; API-03 ACCEPTED / CLOSED; API-04 ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` | API-04 is the active primary API stage. API-03 is closed at exact accepted C5. API remains open through API-06. |',
    'program phase API row',
)
once(
    'DATA = CLOSED\nAPI-01 = ACCEPTED / CLOSED\nAPI-02 = ACCEPTED / CLOSED\nAPI-03 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED',
    'DATA = CLOSED\nAPI-01 = ACCEPTED / CLOSED\nAPI-02 = ACCEPTED / CLOSED\nAPI-03 = ACCEPTED / CLOSED\nAPI-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED',
    'current primary block',
)
once('  → API-03\n  → API-04', '  → API-03 CLOSED\n  → API-04 ACTIVE', 'governed path')
once(
    'While API-03 is the active primary API stage, the following may proceed without changing `API-03 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`. API-03 itself must first reconcile/rebase to the exact accepted API-02 C13 bytes before seal and independent acceptance:',
    'While API-04 is the active primary API stage, the following may proceed without changing `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`. API-03 is accepted/closed at exact C5 and is the governed predecessor for API-04:',
    'parallel work current stage',
)

top = """**API-03 authoritative acceptance and closure (2026-09-01):** exact resealed candidate `EPD2_API03_SERVICE_TO_SERVICE_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C5.zip`, SHA-256 `5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55`, size `43,300,451` bytes, passed the independent sealed GitHub Actions workflow `.github/workflows/api03-accept.yml`, authoritative run `33511256210`, job `99867183151`, provenance commit `412a6fb3e5445a92d3792ceecd17649e4afd132d`, conclusion `success`. The run emitted `API03_RESULT:PASS:validation/api03/authoritative_acceptance_result.json`; all `22/22` acceptance gates completed successfully with no failed or environment-blocked gate. Exact live evidence includes `99/99` API-03 tests with `0` failed and `0` skipped, PostgreSQL `16.15` / `server_version_num=160015`, workspace cryptography `46.0.7`, isolated offline cryptography `49.0.0`, governed R11 V23 PASS, real multi-process mTLS/replay topology PASS, and SEC-01 repository guard PASS. The first C5 seal SHA `8a62ea6c8ab1fb441811e476af0060f4b6c5374002312bb04e5a68968b6a3ea8` was correctly rejected by authoritative run `33510911890` because builder-side `py_compile` created an unaccounted verifier `.pyc` after seal verification; it is superseded by the corrected reseal above with runtime and sealed workflow unchanged. Authoritative evidence artifact `api03-c5-authoritative-acceptance-33511256210`, artifact ID `9801733668`, GitHub artifact digest `sha256:ccbf76b448ec634803330c0f5575a44bf50f50eae195cacfcfdfe53789987a78`. The governance decision is recorded in `docs/api/API-03/API03_C5_ACCEPTANCE_RECORD.json`. **API-03 is therefore `ACCEPTED / CLOSED`.** The candidate's self-state `CANDIDATE_NOT_ACCEPTED` remains the intentional no-self-acceptance safeguard in the sealed bytes and is superseded only by the independent post-run governance decision. No open API-03 blocker remains. `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` is now the next primary API stage. The API layer remains open until API-06; no production-readiness, legal-activation, final-security, BSI/CC or EAL4 certification claim follows from this transition.\n\n"""
marker = 'On 2026-08-26 API-01 completed independent authoritative acceptance.'
if s.count(marker) != 1:
    raise AssertionError('top transition marker mismatch')
s = s.replace(marker, top + marker, 1)

detail = """### API-03 C5 authoritative transition — 2026-09-01

- **Previous state:** `API-03 ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`; sealed candidate self-state `CANDIDATE_NOT_ACCEPTED`.
- **New state:** `API-03 ACCEPTED / CLOSED`.
- **Governing candidate:** `EPD2_API03_SERVICE_TO_SERVICE_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C5.zip`.
- **Candidate SHA-256:** `5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55`.
- **Candidate size:** `43,300,451` bytes.
- **Corrected seal/reseal builder:** run `33511140504`, provenance commit `9d4292eb38a388c85ac0205a02c47d4a525ddcb1`, artifact ID `9801661733`, outer digest `sha256:b85551b811c0a75358b9f5c717830a5a3306b82d473fd6c49e0c0a9e6373d0e3`; complete seal accounting covers `4125` files.
- **Superseded failed seal:** SHA-256 `8a62ea6c8ab1fb441811e476af0060f4b6c5374002312bb04e5a68968b6a3ea8`, builder run `33510681168`, rejected by authoritative run `33510911890` because `py_compile` created unaccounted `scripts/__pycache__/api03_verify_seal.cpython-312.pyc` after successful pre-package seal verification. Corrected reseal removed that packaging offender and rebuilt complete manifest/checksums without runtime, governed-test or workflow changes.
- **Technical C4 basis:** SHA-256 `09531e9b64dd66c558e3c2478ea897e020adfd4814a7237cd8eab7f18b568a86`; verification run `33509385291`, job `99861098139`, conclusion `success`; evidence artifact ID `9800985043`, digest `sha256:1a8074c08631910f28833a95cef45d8f85f0b9b0762740a65bfa050f5f80555f`.
- **Authoritative workflow:** `.github/workflows/api03-accept.yml`, exact sealed Git blob `2bc621dd168c5c9fa5bc0782ed2cecdde40a9e82`, SHA-256 `39a04b1a5d57c320f542889d81a5c6e9a2a30e6684d2bae49e4a82cbe5406e8d`; authoritative branch used the same blob for byte-for-byte binding.
- **Authoritative run:** `33511256210`, job `99867183151`, conclusion `success`, provenance commit `412a6fb3e5445a92d3792ceecd17649e4afd132d`.
- **Terminal result:** `API03_RESULT:PASS:validation/api03/authoritative_acceptance_result.json`; `22/22` acceptance gates completed successfully, no failed or environment-blocked gate.
- **Live/runtime evidence:** API-03 `99/99 PASS`, `0` failed, `0` skipped; PostgreSQL `16.15` / `server_version_num=160015`; workspace cryptography `46.0.7`; isolated cryptography `49.0.0` via offline wheelhouse; governed R11 V23 PASS; real multi-process mTLS/replay topology PASS; SEC-01 repository guard PASS.
- **Accepted predecessor:** API-02 C13 SHA-256 `9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9`, authoritative run `33497989489`, `ACCEPTED / CLOSED`.
- **Authoritative evidence artifact:** `api03-c5-authoritative-acceptance-33511256210`, artifact ID `9801733668`, size `9,563` bytes, digest `sha256:ccbf76b448ec634803330c0f5575a44bf50f50eae195cacfcfdfe53789987a78`, created `2026-09-01T13:05:41Z`, expires `2026-11-30T13:04:44Z`.
- **Acceptance decision:** `docs/api/API-03/API03_C5_ACCEPTANCE_RECORD.json`.
- **No-self-acceptance resolution:** `CANDIDATE_NOT_ACCEPTED` remains inside sealed C5 intentionally; independent authoritative acceptance plus the post-run governance record establishes canonical `ACCEPTED / CLOSED`.
- **Open blockers for API-03:** none.
- **Scope consequence:** API-03 is closed at exact corrected C5. API remains open through API-06. No production-readiness, legal-activation, final-security, BSI/CC or EAL4 certification claim follows.
- **Next permitted primary stage:** `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`.

"""
section7 = '---\n\n## 7. Branch / reconciliation discipline'
if s.count(section7) != 1:
    raise AssertionError('section 7 marker mismatch')
s = s.replace(section7, detail + section7, 1)

once(
    '**Primary implementation:** `API-03 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` (`API-01 = ACCEPTED / CLOSED`; `API-02 = ACCEPTED / CLOSED`). API-03 must reconcile/rebase to exact accepted API-02 C13 SHA-256 `9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9` before seal and independent acceptance.',
    '**Primary implementation:** `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED` (`API-01 = ACCEPTED / CLOSED`; `API-02 = ACCEPTED / CLOSED`; `API-03 = ACCEPTED / CLOSED`). API-04 must treat exact accepted API-03 C5 SHA-256 `5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55` as its governed predecessor baseline and requires its own seal and independent authoritative acceptance.',
    'section 9 primary',
)
once(
    '**Governed forward path:** reconcile/rebase active API-03 to the exact accepted API-02 C13 bytes, complete API-03, seal and independently verify it before any API-03 acceptance/closure claim; then continue API-04 → API-05 → API-06 with independent authoritative acceptance at each stage; close API only after API-06.',
    '**Governed forward path:** complete API-04 against the exact accepted API-03 C5 predecessor, seal and independently verify API-04 before any API-04 acceptance/closure claim; then continue API-05 → API-06 with independent authoritative acceptance at each stage; close API only after API-06.',
    'section 9 forward path',
)
once('API-03 is now the primary API stage; this FRONT work does not constitute FRONT acceptance or final closure.', 'API-04 is now the primary API stage; this FRONT work does not constitute FRONT acceptance or final closure.', 'section 9 FRONT')
once('Neither accepted PILOT stage changes the current API-03 primary position, claims production readiness/legal activation, or forces immediate INTEGRATION-01 advancement.', 'Neither accepted PILOT stage changes the current API-04 primary position, claims production readiness/legal activation, or forces immediate INTEGRATION-01 advancement.', 'section 9 PILOT')
once('The current primary implementation position is `API-03 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`; FRONT-MOBILE-02 is not started, FRONT is not closed, and no mobile/production/security readiness is claimed.', 'The current primary implementation position is `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`; API-03 is `ACCEPTED / CLOSED`; FRONT-MOBILE-02 is not started, FRONT is not closed, and no mobile/production/security readiness is claimed.', 'mobile current primary')

p.write_text(s, encoding='utf-8')

rec = json.loads(Path('docs/api/API-03/API03_C5_ACCEPTANCE_RECORD.json').read_text())
assert rec['decision'] == 'ACCEPTED_CLOSED'
assert rec['candidate']['sha256'] == '5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55'
assert rec['authoritative']['run_id'] == 33511256210
assert rec['open_blockers'] == []
assert '`API-03 ACCEPTED / CLOSED; API-04 ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`' in s
assert 'API-03 = ACCEPTED / CLOSED\nAPI-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED' in s
assert '### API-03 C5 authoritative transition — 2026-09-01' in s
assert '**Primary implementation:** `API-04 = ACTIVE / IN DEVELOPMENT / NOT ACCEPTED`' in s
assert 'API03_RESULT:PASS:validation/api03/authoritative_acceptance_result.json' in s
print('API03_C5_REGISTER_PATCH:PASS')
