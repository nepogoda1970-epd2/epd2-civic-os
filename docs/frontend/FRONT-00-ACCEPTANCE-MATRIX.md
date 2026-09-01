# FRONT-00 Acceptance Matrix

| Requirement                 | Evidence                                            | Candidate result                   |
| --------------------------- | --------------------------------------------------- | ---------------------------------- |
| Five faithful migrations    | `migrated-fixtures.tsx`, source mapping             | implemented                        |
| Preserve visual composition | design report + 15 reviewed viewport snapshots      | implemented; external gate remains |
| Honest reporting language   | source/migration/showcase distinction               | implemented                        |
| Minimum component catalogue | reusable components + documented native patterns    | implemented                        |
| Rendered behavior tests     | 13 Testing Library cases                            | implemented                        |
| Browser visual regression   | Playwright, 15 viewport/page cases                  | 15/15 local compare passed         |
| Automated accessibility     | axe + keyboard/landmark/dialog/reduced-motion cases | implemented                        |
| Ten workspace registry      | typed catalogue and architecture tests              | implemented                        |
| WS-03 isolation             | storage/telemetry denial tests                      | implemented                        |
| Mobile App client channel   | typed profile; workspace/origin count tests         | declared; inactive                 |
| Mobile capability boundary  | WS-02 + limited WS-05; privileged deny tests        | declared; inactive                 |
| Citizen-office dependency   | WS-05 request status → direct owner PACK-33 test    | corrected; inactive                |
| Mobile voting handoff       | system-browser/isolation/return-status tests        | policy only; no API                |
| Mobile push/security        | neutral payload/offline/activation tests            | policy only; no provider           |
| Mobile accessibility        | responsive foundation + documented native gates     | partial foundation; not certified  |
| No business/backend scope   | no API; disabled fixture actions                    | implemented                        |
| Existing suites retained    | node tests remain; Vitest supplements them          | implemented                        |
| Repository/canon versions   | 0.9.0 / 0.7.0                                       | unchanged                          |
| External CI decision        | GitHub Actions                                      | pending                            |

This matrix records candidate evidence only. It is not PASS, certification,
production readiness, or legal activation.
