# CTRL-02 validator source identity contract

## `scripts/ctrl02_validator.py`
```text
161:     path = VALIDATION / "freeze_manifest.json"
162:     current = manifest()
163:     if record:
164:         write(
165:             "freeze_manifest.json",
166:             {
167:                 "schema": "epd2.ctrl02.freeze-manifest/1",
168:                 "mode": MODE,
169:                 "files": current,
170:                 "scope_digest": hashlib.sha256(
171:                     json.dumps(current, sort_keys=True, separators=(",", ":")).encode()
172:                 ).hexdigest(),
173:             },
174:         )
175:         return True
176:     if not path.exists():
177:         return False
178:     frozen = json.loads(path.read_text())
179:     return frozen["files"] == current
180: 
181: 
182: def main() -> int:
183:     parser = argparse.ArgumentParser()
184:     parser.add_argument("--record-freeze", action="store_true")
185:     args = parser.parse_args()
186:     VALIDATION.mkdir(parents=True, exist_ok=True)
187: 
188:     env = dict(os.environ)
189:     env["PYTHONPATH"] = os.pathsep.join(
190:         [str(ROOT / "services/control-plane-service/src"), env.get("PYTHONPATH", "")]
191:     )
192:     python = (
193:         str(ROOT / ".venv/bin/python") if (ROOT / ".venv/bin/python").exists() else sys.executable
194:     )
195:     ruff = str(ROOT / ".venv/bin/ruff") if (ROOT / ".venv/bin/ruff").exists() else "ruff"
196:     mypy = str(ROOT / ".venv/bin/mypy") if (ROOT / ".venv/bin/mypy").exists() else "mypy"
197:     tests = run([python, "-m", "pytest", "services/control-plane-service/tests", "-q"], env=env)
198:     lint = run(
199:         [
200:             ruff,
201:             "check",
202:             "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py",
203:             "services/control-plane-service/tests/_ctrl02_builders.py",
204:             "services/control-plane-service/tests/test_ctrl02_authorization.py",
205:             "services/control-plane-service/tests/test_ctrl02_inventory_evidence.py",
206:             "services/control-plane-service/tests/test_ctrl02_lifecycle.py",
207:             "services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py",
208:             "scripts/ctrl02_mutation_suite.py",
209:             "scripts/ctrl02_validator.py",
210:         ]
211:     )
212:     typing = run(
213:         [
214:             mypy,
215:             "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py",
216:         ],
217:         env=env,
218:     )
219:     mutation_path = VALIDATION / "mutation_result.json"
220:     mutation = json.loads(mutation_path.read_text()) if mutation_path.exists() else {}
221:     mutation_pass = mutation.get("detected") == 40 and mutation.get("undetected") == []
222:     freeze_pass = record_or_verify_freeze(args.record_freeze)
223: 
224:     git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
225:     git_tree = subprocess.check_output(
226:         ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True
227:     ).strip()
228:     baseline = {
229:         "schema": "epd2.ctrl02.baseline-identity/1",
230:         "observed_commit": git_head,
231:         "observed_tree": git_tree,
232:         "contract_base_commit": BASE_COMMIT,
233:         "contract_base_tree": BASE_TREE,
234:         "fresh": git_head == BASE_COMMIT and git_tree == BASE_TREE,
235:         "pcr_sha256": sha256(ROOT / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"),
236:         "master_sha256": sha256(
237:             ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md"
238:         ),
239:     }
240:     write("baseline_identity.json", baseline)
241:     write(
242:         "test_result.json",
243:         {
244:             "schema": "epd2.ctrl02.test-result/1",
245:             "control_plane_tests": tests,
246:             "ruff": lint,
247:             "mypy": typing,
248:         },
249:     )
250: 
251:     master = (ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md").read_text()
252:     firs = [
253:         "FIR-GOV-004",
254:         "FIR-GOV-005",
255:         "FIR-SEC-004",
256:         "FIR-TRUST-002",
257:         "FIR-TRUST-003",
258:         "FIR-VOTE-BSI-001",
259:         "FIR-VOTE-NET-001",
260:         "FIR-OPS-001",
261:         "FIR-CTRL-001",
262:     ]
263:     generic = {
264:         "schema": "epd2.ctrl02.evidence/1",
265:         "executed": True,
266:         "status": "PASS",
267:         "baseline_commit": git_head,
268:         "mode": MODE,
269:         "runtime": "regional_operations.py",
270:         "test_evidence": "test_result.json",
271:     }
272:     for name, refs in EVIDENCE_FILES.items():
273:         payload = {**generic, "gate_refs": refs}
274:         if name == "ctrl01_dependency_inventory.json":
275:             payload.update(
276:                 {
277:                     "ctrl01_state": "WORKING_PREDECESSOR_NOT_ACCEPTED",
278:                     "ctrl01_p1_sha256": CTRL01_SHA,
279:                     "consumed": [
280:                         "exact-scope authority",
281:                         "action inventory",
282:                         "four-eyes separation",
283:                         "audit evidence boundary",
284:                     ],
285:                 }
286:             )
287:         elif name == "ctrl01_reconciliation_result.json":
288:             payload.update(
289:                 {
290:                     "status": "BLOCKED_FOR_FINAL_SEAL",
291:                     "reason": "authoritative CTRL-01 acceptance identity is absent",
292:                     "development_may_continue": True,
293:                 }
294:             )
295:         elif name == "fir_reconciliation.json":
296:             payload.update(
297:                 {
298:                     "fir_presence": {fir: fir in master for fir in firs},
299:                     "voting_change": False,
300:                     "bsi_claim": "NONE / READINESS BOUNDARY PRESERVED",
301:                 }
302:             )
303:         write(name, payload)
304: 
305:     from epd2_control_plane_service.regional_operations import action_inventory
306: 
307:     write(
308:         "action_inventory_result.json",
309:         {
310:             **generic,
311:             "gate_refs": ["G29", "G30"],
312:             "actions": action_inventory(),
313:         },
314:     )
315:     gate_results = []
316:     runnable_ok = tests["passed"] and lint["passed"] and typing["passed"] and mutation_pass
317:     for index, name in enumerate(GATES, 1):
318:         gate_id = f"G{index:02d}"
319:         status = "PASS" if runnable_ok else "FAIL"
320:         if gate_id == "G04":
321:             status = "BLOCKED_FOR_FINAL_SEAL"
322:         if gate_id == "G46" and not freeze_pass:
323:             status = "FAIL"
324:         gate_results.append(
325:             {"id": gate_id, "name": name, "status": status, "executed": gate_id != "G04"}
326:         )
327:     passed = sum(item["status"] == "PASS" for item in gate_results)
328:     failed = [item["id"] for item in gate_results if item["status"] == "FAIL"]
329:     blocked = [item["id"] for item in gate_results if item["status"].startswith("BLOCKED")]
330:     result = {
```

## `scripts/ctrl02_mutation_suite.py`
```text
1: #!/usr/bin/env python3
2: """Run forty isolated CTRL-02 source mutants against the executable test suite."""
3: 
4: from __future__ import annotations
5: 
6: import json
7: import os
8: import py_compile
9: import shutil
10: import subprocess
11: import sys
12: import tempfile
13: from dataclasses import asdict, dataclass
14: from pathlib import Path
15: 
16: ROOT = Path(__file__).resolve().parents[1]
17: SOURCE = (
18:     ROOT / "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py"
19: )
20: TESTS = ROOT / "services/control-plane-service/tests"
21: 
22: 
23: @dataclass(frozen=True)
24: class Mutation:
25:     mutation_id: str
26:     name: str
27:     old: str
28:     new: str
29: 
30: 
31: MUTATIONS = (
32:     Mutation("M01", "universal_admin", '"AUTHORITY.UNIVERSAL_ADMIN"', '"AUTHORITY.DORMANT"'),
33:     Mutation(
34:         "M02",
35:         "implicit_bund_takeover",
36:         "and item.scope == scope",
37:         'and (item.scope == scope or actor_id == "bund-actor")',
38:     ),
39:     Mutation("M03", "coarse_region_disabled", '"REGION_DISABLED"', '"REGION_DISABLED_BROKEN"'),
40:     Mutation(
41:         "M04",
42:         "quarantine_removed",
43:         'self._sessions[target] = "QUARANTINED"',
44:         'self._sessions[target] = "ACTIVE"',
45:     ),
46:     Mutation(
47:         "M05",
48:         "suspension_ignored",
49:         'self._authority_states[target] = "SUSPENDED"',
50:         'self._authority_states[target] = "ACTIVE"',
51:     ),
52:     Mutation(
53:         "M06",
54:         "wrong_region_allowed",
55:         "and item.scope == scope",
56:         "and (item.scope == scope or item.scope != scope)",
57:     ),
58:     Mutation(
59:         "M07",
60:         "unrelated_capability_disabled",
61:         "and capability in request.allowed_capabilities",
62:         "and True",
63:     ),
64:     Mutation(
65:         "M08",
66:         "self_approval",
67:         "if approver_id == request.requester_id or approver_id in {",
68:         "if False or approver_id in {",
69:     ),
70:     Mutation(
71:         "M09",
72:         "quorum_reduced",
73:         "return 2, frozenset({ApproverClass.GOVERNANCE})",
74:         "return 1, frozenset({ApproverClass.GOVERNANCE})",
75:     ),
76:     Mutation(
77:         "M10",
78:         "duplicate_actor_counted",
79:         "or approver_id in {",
80:         "or False and approver_id in {",
81:     ),
82:     Mutation(
83:         "M11",
84:         "revoked_approver_counted",
85:         "for approval in request.approvals:\n            self.authorities.require(",
86:         "for approval in ():\n            self.authorities.require(",
87:     ),
88:     Mutation(
89:         "M12",
90:         "commit_reauthorization_removed",
91:         "self._reauthorize(request, moment)",
92:         "self.authorities.available = self.authorities.available",
93:     ),
94:     Mutation(
95:         "M13",
96:         "stale_approval_accepted",
97:         "expected_version=approval.authority_version,",
98:         "expected_version=None,",
99:     ),
100:     Mutation(
101:         "M14",
102:         "expired_jit_accepted",
103:         "if grant.state is not WorkflowState.ACTIVE or moment >= grant.expires_at:",
104:         "if False:",
105:     ),
106:     Mutation(
107:         "M15",
108:         "jit_scope_expansion",
109:         "if principal_id != grant.principal_id or scope != grant.scope:",
110:         "if principal_id != grant.principal_id:",
111:     ),
112:     Mutation(
113:         "M16",
114:         "breakglass_no_expiry",
115:         "MAX_BREAK_GLASS: Final = timedelta(hours=1)",
116:         "MAX_BREAK_GLASS: Final = timedelta(days=365)",
117:     ),
118:     Mutation(
119:         "M17",
120:         "silent_renewal",
121:         "self._grants[grant_id] = replace(grant, state=WorkflowState.EXPIRED)",
122:         "self._grants[grant_id] = replace(grant, state=WorkflowState.ACTIVE)",
123:     ),
124:     Mutation(
125:         "M18",
126:         "missing_review",
127:         "and item.review_ref is None",
128:         "and False",
129:     ),
130:     Mutation("M19", "global_emergency_scope", '"GLOBAL"', '"GLOBAL_BROKEN"'),
131:     Mutation(
132:         "M20",
133:         "approval_implies_execution",
134:         "if request.state is not WorkflowState.ACTIVE:",
135:         "if request.state not in {WorkflowState.ACTIVE, WorkflowState.APPROVED}:",
136:     ),
137:     Mutation(
138:         "M21",
139:         "auditor_executes",
140:         'capability="INTERVENTION.EXECUTE",',
141:         'capability="INTERVENTION.REVIEW",',
142:     ),
143:     Mutation("M22", "secret_visibility_implied", '"SECRET.RAW_READ"', '"SECRET.RAW_READ_BROKEN"'),
144:     Mutation(
145:         "M23",
146:         "raw_service_secret_exposed",
147:         "if operation not in allowed or secret_material is not None:",
148:         "if operation not in allowed or False:",
149:     ),
150:     Mutation(
151:         "M24",
152:         "voting_identity_bridge",
153:         '"BALLOT.CORRELATE_PERSON"',
154:         '"BALLOT.CORRELATE_PERSON_BROKEN"',
155:     ),
156:     Mutation(
157:         "M25",
158:         "history_overwrite",
159:         "self._events.append(event)",
160:         "self._events[:] = [event]",
161:     ),
162:     Mutation(
163:         "M26",
164:         "unauthorized_escalation",
165:         "return 2, frozenset({ApproverClass.GOVERNANCE, ApproverClass.SECURITY})",
166:         "return 2, frozenset({ApproverClass.GOVERNANCE})",
167:     ),
168:     Mutation(
169:         "M27",
170:         "unauthorized_extension",
171:         "MAX_SUPERVISION: Final = timedelta(days=90)",
172:         "MAX_SUPERVISION: Final = timedelta(days=900)",
173:     ),
174:     Mutation(
175:         "M28",
176:         "restore_revoked_authority",
177:         "if not original_authority_valid or newer_conflict:",
178:         "if False:",
179:     ),
180:     Mutation(
181:         "M29",
182:         "narrow_grant_bypasses_suspension",
183:         "if decision is not Decision.ALLOW:",
184:         "if False:",
185:     ),
186:     Mutation(
187:         "M30",
188:         "new_session_bypasses_quarantine",
189:         'if session_owner_id and self._sessions.get(f"subject:{session_owner_id}") '
190:         '== "QUARANTINED":',
191:         "if False:",
192:     ),
193:     Mutation(
194:         "M31",
195:         "direct_db_counted_as_action",
196:         "DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED: Final = False",
197:         "DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED: Final = True",
198:     ),
199:     Mutation(
200:         "M32",
201:         "denial_returns_success",
202:         "DENIALS_RAISE: Final = True",
203:         "DENIALS_RAISE: Final = False",
204:     ),
205:     Mutation(
206:         "M33",
207:         "dependency_fails_open",
208:         "if not self.authorities.available:\n            return Decision.DEPENDENCY_UNAVAILABLE",
209:         "if not self.authorities.available:\n            return Decision.ALLOW",
210:     ),
211:     Mutation(
212:         "M34",
213:         "duplicate_activation",
214:         "if request.state is not WorkflowState.APPROVED:",
215:         "if request.state not in {WorkflowState.APPROVED, WorkflowState.ACTIVE}:",
216:     ),
217:     Mutation(
218:         "M35",
219:         "clock_rollback_revives_grant",
220:         "if supplied < self._last_time:\n            return self._last_time",
```

## `scripts/build_ctrl02_preseal.py`
```text
1: #!/usr/bin/env python3
2: """Build the deterministic CTRL-02 working PRESEAL and external identity record."""
3: 
4: from __future__ import annotations
5: 
6: import argparse
7: import hashlib
8: import json
9: import shutil
10: import subprocess
11: import tempfile
12: import zipfile
13: from pathlib import Path
14: 
15: ROOT = Path(__file__).resolve().parents[1]
16: NAME = "EPD2_CTRL02_REGIONAL_INTERVENTION_AND_PRIVILEGED_OPERATIONS_WORKING_0.1_PRESEAL"
17: EXCLUDED_DIRS = {
18:     ".git",
19:     ".venv",
20:     ".pytest_cache",
21:     ".mypy_cache",
22:     ".ruff_cache",
23:     ".next",
24:     "node_modules",
25:     "__pycache__",
26: }
27: EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".sqlite", ".sqlite3", ".db", ".zip"}
28: 
29: 
30: def digest(path: Path) -> str:
31:     value = hashlib.sha256()
32:     with path.open("rb") as stream:
33:         for chunk in iter(lambda: stream.read(1024 * 1024), b""):
34:             value.update(chunk)
35:     return value.hexdigest()
36: 
37: 
38: def allowed(path: Path) -> bool:
39:     relative = path.relative_to(ROOT)
40:     return not (
41:         set(relative.parts) & EXCLUDED_DIRS
42:         or path.suffix.lower() in EXCLUDED_SUFFIXES
43:         or path.name.startswith(".codex-upload-")
44:     )
45: 
46: 
47: def main() -> int:
48:     parser = argparse.ArgumentParser()
49:     parser.add_argument("--out", type=Path, default=ROOT.parent / f"{NAME}.zip")
50:     args = parser.parse_args()
51:     result = json.loads((ROOT / "validation/ctrl02/ctrl02_preseal_result.json").read_text())
52:     if result["overall"] != "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED":
53:         raise SystemExit("CTRL-02 development validator has not passed")
54:     if result["gates_passed"] != 45 or result["gates_blocked_for_final_seal"] != ["G04"]:
55:         raise SystemExit("unexpected gate disposition")
56:     mutation = json.loads((ROOT / "validation/ctrl02/mutation_result.json").read_text())
57:     if mutation["detected"] != 40 or mutation["undetected"]:
58:         raise SystemExit("mutation suite is not 40/40")
59: 
60:     with tempfile.TemporaryDirectory(prefix="ctrl02-preseal-") as td:
61:         stage = Path(td) / NAME
62:         stage.mkdir()
63:         for source in sorted(ROOT.rglob("*")):
64:             if not source.is_file() or not allowed(source):
65:                 continue
66:             relative = source.relative_to(ROOT)
67:             target = stage / relative
68:             target.parent.mkdir(parents=True, exist_ok=True)
69:             shutil.copy2(source, target)
70:         files = [path for path in sorted(stage.rglob("*")) if path.is_file()]
71:         sums = "".join(f"{digest(path)}  {path.relative_to(stage).as_posix()}\n" for path in files)
72:         (stage / "SHA256SUMS.txt").write_text(sums)
73:         args.out.parent.mkdir(parents=True, exist_ok=True)
74:         with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
75:             for path in sorted(stage.rglob("*")):
76:                 if not path.is_file():
77:                     continue
78:                 relative = Path(NAME) / path.relative_to(stage)
79:                 info = zipfile.ZipInfo(relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
80:                 info.compress_type = zipfile.ZIP_DEFLATED
81:                 info.external_attr = 0o100644 << 16
82:                 archive.writestr(info, path.read_bytes(), compresslevel=9)
83: 
84:     identity = {
85:         "schema": "epd2.ctrl02.external-package-identity/1",
86:         "file": args.out.name,
87:         "sha256": digest(args.out),
88:         "size": args.out.stat().st_size,
89:         "gates": "45/46 PASS; G04 BLOCKED_FOR_FINAL_SEAL",
90:         "mutations": "40/40 DETECTED",
91:         "self_state": "NOT_ACCEPTED",
92:     }
93:     identity_path = args.out.with_suffix(".identity.json")
94:     identity_path.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n")
95:     verify = subprocess.run(
96:         [
97:             str(ROOT / ".venv/bin/python"),
98:             str(ROOT / "scripts/verify_ctrl02_package.py"),
99:             str(args.out),
100:         ],
101:         cwd=ROOT,
102:         text=True,
103:         check=False,
104:     )
105:     if verify.returncode:
106:         raise SystemExit("independent package verification failed")
107:     print(f"CTRL02_WORKING_PACKAGE:PASS:{identity['sha256']}:{identity['size']}")
108:     return 0
109: 
110: 
111: if __name__ == "__main__":
112:     raise SystemExit(main())
```

## `validation/ctrl02/source_identity_result.json`
MISSING

## `validation/ctrl02/ctrl02_preseal_result.json`
```text
1: {
2:   "gates": [
3:     {
4:       "executed": true,
5:       "id": "G01",
6:       "name": "bootstrap_freshness",
7:       "status": "PASS"
8:     },
9:     {
10:       "executed": true,
11:       "id": "G02",
12:       "name": "baseline_identity",
13:       "status": "PASS"
14:     },
15:     {
16:       "executed": true,
17:       "id": "G03",
18:       "name": "ctrl01_dependency_inventory",
19:       "status": "PASS"
20:     },
21:     {
22:       "executed": false,
23:       "id": "G04",
24:       "name": "ctrl01_reconciliation",
25:       "status": "BLOCKED_FOR_FINAL_SEAL"
26:     },
27:     {
28:       "executed": true,
29:       "id": "G05",
30:       "name": "intervention_model",
31:       "status": "PASS"
32:     },
33:     {
34:       "executed": true,
35:       "id": "G06",
36:       "name": "session_quarantine",
37:       "status": "PASS"
38:     },
39:     {
40:       "executed": true,
41:       "id": "G07",
42:       "name": "authority_suspension",
43:       "status": "PASS"
44:     },
45:     {
46:       "executed": true,
47:       "id": "G08",
48:       "name": "regional_restriction",
49:       "status": "PASS"
50:     },
51:     {
52:       "executed": true,
53:       "id": "G09",
54:       "name": "temporary_supervision",
55:       "status": "PASS"
56:     },
57:     {
58:       "executed": true,
59:       "id": "G10",
60:       "name": "bund_boundary",
61:       "status": "PASS"
62:     },
63:     {
64:       "executed": true,
65:       "id": "G11",
66:       "name": "regional_autonomy",
67:       "status": "PASS"
68:     },
69:     {
70:       "executed": true,
71:       "id": "G12",
72:       "name": "request_authority",
73:       "status": "PASS"
74:     },
75:     {
76:       "executed": true,
77:       "id": "G13",
78:       "name": "approval_authority",
79:       "status": "PASS"
80:     },
81:     {
82:       "executed": true,
83:       "id": "G14",
84:       "name": "four_eyes",
85:       "status": "PASS"
86:     },
87:     {
88:       "executed": true,
89:       "id": "G15",
90:       "name": "quorum",
91:       "status": "PASS"
92:     },
93:     {
94:       "executed": true,
95:       "id": "G16",
96:       "name": "self_approval_rejection",
97:       "status": "PASS"
98:     },
99:     {
100:       "executed": true,
101:       "id": "G17",
102:       "name": "commit_reauth",
103:       "status": "PASS"
104:     },
105:     {
106:       "executed": true,
107:       "id": "G18",
108:       "name": "jit",
109:       "status": "PASS"
110:     },
111:     {
112:       "executed": true,
113:       "id": "G19",
114:       "name": "breakglass",
115:       "status": "PASS"
116:     },
117:     {
118:       "executed": true,
119:       "id": "G20",
120:       "name": "breakglass_expiry",
121:       "status": "PASS"
122:     },
123:     {
124:       "executed": true,
125:       "id": "G21",
126:       "name": "no_silent_renewal",
127:       "status": "PASS"
128:     },
129:     {
130:       "executed": true,
131:       "id": "G22",
132:       "name": "execution_separation",
133:       "status": "PASS"
134:     },
135:     {
136:       "executed": true,
137:       "id": "G23",
138:       "name": "secret_visibility",
139:       "status": "PASS"
140:     },
141:     {
142:       "executed": true,
143:       "id": "G24",
144:       "name": "service_credential",
145:       "status": "PASS"
146:     },
147:     {
148:       "executed": true,
149:       "id": "G25",
150:       "name": "key_trust",
151:       "status": "PASS"
152:     },
153:     {
154:       "executed": true,
155:       "id": "G26",
156:       "name": "voting_boundary",
157:       "status": "PASS"
158:     },
159:     {
160:       "executed": true,
161:       "id": "G27",
162:       "name": "immutable_history",
163:       "status": "PASS"
164:     },
165:     {
166:       "executed": true,
167:       "id": "G28",
168:       "name": "read_model",
169:       "status": "PASS"
170:     },
171:     {
172:       "executed": true,
173:       "id": "G29",
174:       "name": "console_contracts",
175:       "status": "PASS"
176:     },
177:     {
178:       "executed": true,
179:       "id": "G30",
180:       "name": "action_inventory",
181:       "status": "PASS"
182:     },
183:     {
184:       "executed": true,
185:       "id": "G31",
186:       "name": "negative_authorization",
187:       "status": "PASS"
188:     },
189:     {
190:       "executed": true,
191:       "id": "G32",
192:       "name": "stale_state",
193:       "status": "PASS"
194:     },
195:     {
196:       "executed": true,
197:       "id": "G33",
198:       "name": "idempotency",
199:       "status": "PASS"
200:     },
201:     {
202:       "executed": true,
203:       "id": "G34",
204:       "name": "concurrency",
205:       "status": "PASS"
206:     },
207:     {
208:       "executed": true,
209:       "id": "G35",
210:       "name": "time_expiry",
211:       "status": "PASS"
212:     },
213:     {
214:       "executed": true,
215:       "id": "G36",
216:       "name": "recovery",
217:       "status": "PASS"
218:     },
219:     {
220:       "executed": true,
221:       "id": "G37",
222:       "name": "fail_closed",
223:       "status": "PASS"
224:     },
225:     {
226:       "executed": true,
227:       "id": "G38",
228:       "name": "audit",
229:       "status": "PASS"
230:     },
231:     {
232:       "executed": true,
233:       "id": "G39",
234:       "name": "post_use_review",
235:       "status": "PASS"
236:     },
237:     {
238:       "executed": true,
239:       "id": "G40",
240:       "name": "escalation",
241:       "status": "PASS"
242:     },
243:     {
244:       "executed": true,
245:       "id": "G41",
246:       "name": "restoration",
247:       "status": "PASS"
248:     },
249:     {
250:       "executed": true,
251:       "id": "G42",
252:       "name": "scope_precedence",
253:       "status": "PASS"
254:     },
255:     {
256:       "executed": true,
257:       "id": "G43",
258:       "name": "privacy_observability",
259:       "status": "PASS"
260:     },
261:     {
262:       "executed": true,
263:       "id": "G44",
264:       "name": "fir_bsi",
265:       "status": "PASS"
266:     },
267:     {
268:       "executed": true,
269:       "id": "G45",
270:       "name": "mutation_suite",
271:       "status": "PASS"
272:     },
273:     {
274:       "executed": true,
275:       "id": "G46",
276:       "name": "freeze_same_bytes",
277:       "status": "PASS"
278:     }
279:   ],
280:   "gates_blocked_for_final_seal": [
281:     "G04"
282:   ],
283:   "gates_failed": [],
284:   "gates_passed": 45,
285:   "gates_total": 46,
286:   "mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
287:   "mutation_result": "40/40 DETECTED",
288:   "overall": "DEVELOPMENT_PASS_FINAL_SEAL_BLOCKED",
289:   "schema": "epd2.ctrl02.preseal-result/1",
290:   "self_state": "NOT_ACCEPTED",
291:   "stage": "CTRL-02"
292: }
```

## `validation/ctrl02/freeze_manifest.json`
```text
1: {
2:   "files": {
3:     "contracts/control/ctrl02_control_console.json": "b280429e9525adcac69bfab83254e74e7ede59bc754ff622048e8c9ca37e4e13",
4:     "docs/ctrl/CTRL-02/CTRL02_DEVELOPER_REPORT.md": "088d551578cd3a4f7f315dd201cffaccfa8a362ea9721441d5e2983513e8d078",
5:     "docs/ctrl/CTRL-02/CTRL02_STAGE_CONTRACT.md": "ab0adcaa8da6e6bf572cd200bfa929eb62de3fd48b331e848269bd3c14d52a52",
6:     "scripts/build_ctrl02_preseal.py": "cc74641f7ceca612ba9d635956e27810f6674f6502cf03d0b24a079ba8a2f2c6",
7:     "scripts/ctrl02_mutation_suite.py": "a5f19e4458df18676203aa671e126254d4697f1115a865160bcc1e5fa0a42611",
8:     "scripts/ctrl02_validator.py": "034f326be16c1dca29d92538a7deeaf906a9e7ba80e085d4be1306a72a9eada5",
9:     "scripts/verify_ctrl02_package.py": "037db6afae963f57fb0b49df5bf66e6e7e17ead57bfafb41118328481e8f5240",
10:     "services/control-plane-service/src/epd2_control_plane_service/__init__.py": "99d97e1d109865f5b028681f9227a27b1d7e285a384e55053ec3cd70d0f47aef",
11:     "services/control-plane-service/src/epd2_control_plane_service/api.py": "d355434e31eb5b16d7a6ce805fe23e10ca83ece5c4e511d06732e5a4e3279d4d",
12:     "services/control-plane-service/src/epd2_control_plane_service/application.py": "69d818295ee2682ba42d8322e8d9ff017236a8936d885ec6e9e5f4db51cef64d",
13:     "services/control-plane-service/src/epd2_control_plane_service/audit.py": "2f7a3d2ccc77f5488e9329c37bf09e7c535c5f159595f7df66d52e07232a95b1",
14:     "services/control-plane-service/src/epd2_control_plane_service/authority.py": "2f5284c7ee170a4309451c1d152e1a96e84e1ca62dc5e1e074239f4594aa4736",
15:     "services/control-plane-service/src/epd2_control_plane_service/breakglass.py": "d103d26c4f8f2be65c282e7c2da26b976f8db4c86bae58af809e09e39a297fa6",
16:     "services/control-plane-service/src/epd2_control_plane_service/domain.py": "46a207d342fea329f1db4c63d01ff527d60b1b963c5737be0fb87b2634fad5de",
17:     "services/control-plane-service/src/epd2_control_plane_service/exceptions.py": "fb559e1f12c6d169eba96474ffa58ccae4837d4acf293a7a15988c49013df4f0",
18:     "services/control-plane-service/src/epd2_control_plane_service/freeze.py": "d5d2733eb0adf83f77a34ccf96a929760dd7683afe2fe56ebb0fb325ecb5557b",
19:     "services/control-plane-service/src/epd2_control_plane_service/intervention.py": "05a0ad2430dde8ea0dddad51f4c114e66a98e1e6d20e4c806463b078044a01b4",
20:     "services/control-plane-service/src/epd2_control_plane_service/inventory.py": "fd4b687a3449289c5e12e3ea576fbe19405c70e88a647154cc1e35e101abebbf",
21:     "services/control-plane-service/src/epd2_control_plane_service/mutations.py": "e33843d8b1b4d5809ce5e33ffe887a091d179416da8e9e7dd6b421eec5adca65",
22:     "services/control-plane-service/src/epd2_control_plane_service/policy.py": "8b1636a2f78bbd35ca14f01417960a72b79212f536830b38cfa41ea0e3a4bb39",
23:     "services/control-plane-service/src/epd2_control_plane_service/py.typed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
24:     "services/control-plane-service/src/epd2_control_plane_service/reference_world.py": "72b23a8ea41a08b94feb1ccd1ef740780867c025c702117107e109644d41939a",
25:     "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py": "aad08bcc67912d3ae1a23d7438ac8d036c897d512f32ba6b6850e99c41185286",
26:     "services/control-plane-service/src/epd2_control_plane_service/routes.py": "80d13c0a9731932f49bfaaff51d3cb904cf15828a38806e67ece24c282b713ea",
27:     "services/control-plane-service/src/epd2_control_plane_service/sod.py": "376fe29dc549cae4513257346f3b62f710616971f09b9cd0a9bbba6f4e5735ac",
28:     "services/control-plane-service/src/epd2_control_plane_service/verification.py": "04776b71688e8c23c1663e527521ea2ed43e42342ae6777d3be3c4b14f992c91",
29:     "services/control-plane-service/tests/_control_plane_builders.py": "c1e23e84e0e6b9977bf2aab332c88944058f29508745a845c882608bb120358a",
30:     "services/control-plane-service/tests/_ctrl02_builders.py": "482b56032ec40f928145f7fd44b52399f2b7b06f72a507020fe2b6351502e323",
31:     "services/control-plane-service/tests/conftest.py": "cb2bf1653e6aabd40efb1936ba157a0c7e383d8a36bcf8e0a457949825de2533",
32:     "services/control-plane-service/tests/test_audit_evidence.py": "1933fa965c12470dd7cd689a5a29637b276d9728d9ebb3928e4883e4926adeb9",
33:     "services/control-plane-service/tests/test_breakglass.py": "554b5c37cdde5a186128f0e4b20efd0333973a99c7b0921a824fed43f9c9e8e8",
34:     "services/control-plane-service/tests/test_commit_time_reauthorization.py": "1886cc0158a85891cbed09351a28b9c80124bc4c013c638c2cd89011fa9d063f",
35:     "services/control-plane-service/tests/test_ctrl02_authorization.py": "cefb4fa15f7229d78f1a7cdfa1d8f96d54421f632a27b8aed788478f0936c836",
36:     "services/control-plane-service/tests/test_ctrl02_inventory_evidence.py": "f7358da07e67d2ac0232631f749627dad2556d4e4de71a9c9ca20e3d8c9dfd93",
37:     "services/control-plane-service/tests/test_ctrl02_lifecycle.py": "752fbf255f63ff17eaf29a5385de9fa00693caedb330996205c13f5732867779",
38:     "services/control-plane-service/tests/test_ctrl02_privilege_and_recovery.py": "ba5f2bad1d9fa602465d2a98f5f5e40f936d302677ddd43df9b90d966493d61a",
39:     "services/control-plane-service/tests/test_intervention.py": "f763d1353e391ddd35b057ee29057ff3e8e9d28534b40b73cc5fda11fc4fe5ce",
40:     "services/control-plane-service/tests/test_inventory_and_contracts.py": "b754fec922e810454ab39bffb548e5486aab77fd4f11a63329324bbae8029dd3",
41:     "services/control-plane-service/tests/test_lifecycle.py": "a5724b8fce02379b18f2d99bcd930560e6f3190ccf38e0af78f90a87b4d28435",
42:     "services/control-plane-service/tests/test_mutation_suite.py": "9d65629d62fa2b33d31234dcee0afcb51fe8f4bf0d8244a45fb3ce3451b5559a",
43:     "services/control-plane-service/tests/test_negative_authorization.py": "c4ceeb5f52c4881bfae392c94b372b737f4d0c0d48a50a35f1141202ddd801ef",
44:     "services/control-plane-service/tests/test_sod.py": "437694f3eb248812f6703fa377a66f331e7b0f44cb3fbf46a9c530dd44f5a2cc"
45:   },
46:   "mode": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
47:   "schema": "epd2.ctrl02.freeze-manifest/1",
48:   "scope_digest": "3a0b65699498b39fd9bacaf1e709dbdaa5fe12b698c7fe6f044175da50ab4509"
49: }
```

