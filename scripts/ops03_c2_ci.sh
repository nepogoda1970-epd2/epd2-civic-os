#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(pwd)
git fetch --no-tags origin main handoff/ops
MAIN=$(git rev-parse origin/main)
TREE=$(git rev-parse origin/main^{tree})
git merge-base --is-ancestor 8db1b85056aad3099fa27e12b29ab9f0a00c4a5b "$MAIN"

# Canonical API-06 prerequisite must remain accepted/closed at the exact accepted identity.
git show "origin/main:docs/api/API-06/API06_C1_ACCEPTANCE_RECORD.json" > "$RUNNER_TEMP/api06-acceptance.json"
jq -e '.decision=="ACCEPTED_CLOSED" and .api_layer_state=="CLOSED" and .candidate.filename=="EPD2_API06_API_LAYER_COMPLETION_AND_PREVIEW_READINESS_CANDIDATE_0.1_C1.zip" and .candidate.sha256=="3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c" and .candidate.size_bytes==44012716 and .candidate.self_accepted==false and .authoritative.run_id==33629147572 and .authoritative.job_id==100243984921 and .authoritative.conclusion=="SUCCESS" and .authoritative.passed_gates==40 and .authoritative.failed_gates==0 and (.open_blockers|length)==0' "$RUNNER_TEMP/api06-acceptance.json"

rm -rf "$RUNNER_TEMP/mainroot" "$RUNNER_TEMP/ops02" "$RUNNER_TEMP/ops03c1" "$RUNNER_TEMP/accepted" "$RUNNER_TEMP/ops03-c2-root" "$RUNNER_TEMP/ops03-c2-evidence" "$RUNNER_TEMP/ops03-c2-build-evidence"
mkdir -p "$RUNNER_TEMP/mainroot" "$RUNNER_TEMP/ops02" "$RUNNER_TEMP/ops03c1" "$RUNNER_TEMP/accepted" "$RUNNER_TEMP/ops03-c2-evidence" "$RUNNER_TEMP/ops03-c2-build-evidence"
git archive origin/main | tar -x -C "$RUNNER_TEMP/mainroot"

OPS02='handoff/OPS/incoming/EPD2_OPS02_PREVIEW_OPERATIONS_DEPLOYMENT_OBSERVABILITY_AND_RECOVERY_CANDIDATE_0.1_C3.zip'
OPS03='handoff/OPS/incoming/EPD2_OPS03_OPERATIONAL_QUALIFICATION_ALERTING_CAPACITY_AND_RECOVERY_REHEARSAL_CANDIDATE_0.1_C1.zip'
git show "origin/handoff/ops:$OPS02" > "$RUNNER_TEMP/accepted/$(basename "$OPS02")"
git show "origin/handoff/ops:$OPS03" > "$RUNNER_TEMP/accepted/$(basename "$OPS03")"
echo 'ac3b543b0cb3a8e45f7d973c841769d0b4c6e7af649a54aee034f3e0b6afc125  '"$RUNNER_TEMP/accepted/$(basename "$OPS02")" | sha256sum -c -
test "$(stat -c%s "$RUNNER_TEMP/accepted/$(basename "$OPS02")")" = '16632939'
echo 'c4f27e2ead50cab2f1513f4af4b8ae500a16a5658b82add7f51cea03abfc2a16  '"$RUNNER_TEMP/accepted/$(basename "$OPS03")" | sha256sum -c -
test "$(stat -c%s "$RUNNER_TEMP/accepted/$(basename "$OPS03")")" = '16810302'
unzip -q "$RUNNER_TEMP/accepted/$(basename "$OPS02")" -d "$RUNNER_TEMP/ops02"
unzip -q "$RUNNER_TEMP/accepted/$(basename "$OPS03")" -d "$RUNNER_TEMP/ops03c1"
export EPD2_OPS03_ACCEPTED_ARTIFACTS="$RUNNER_TEMP/accepted"
echo 'OPS03_C2_INPUT_IDENTITIES:PASS'

ROOT="$RUNNER_TEMP/ops03-c2-root"
python3 scripts/ops03_c2_reconcile.py \
  --main-root "$RUNNER_TEMP/mainroot" \
  --ops02-root "$RUNNER_TEMP/ops02" \
  --ops03-c1-root "$RUNNER_TEMP/ops03c1" \
  --out-root "$ROOT" \
  --main-commit "$MAIN" \
  --main-tree "$TREE" \
  --template handoff/OPS-03/templates/C2/ops03-accept.yml | tee "$RUNNER_TEMP/ops03-c2-reconcile.log"
grep -q '^OPS03_C2_RECONCILE:PASS:' "$RUNNER_TEMP/ops03-c2-reconcile.log"

# C1 carries an obsolete pre-acceptance API-06 subtree as part of its historical
# delta. C2 must inherit the current canonical API-06 authority from fresh main,
# not replay that stale dependency metadata. Restore the whole governed subtree
# before the exact binding is generated and before bytes are frozen.
rm -rf "$ROOT/docs/api/API-06"
mkdir -p "$ROOT/docs/api/API-06"
cp -a "$RUNNER_TEMP/mainroot/docs/api/API-06/." "$ROOT/docs/api/API-06/"
diff -qr "$RUNNER_TEMP/mainroot/docs/api/API-06" "$ROOT/docs/api/API-06"
echo 'OPS03_C2_CANONICAL_API06_RESTORE:PASS'

# C1 was intentionally blocked at G05 while API-06 was NEXT. C2 rebinds G05 to
# the exact accepted/closed API-06 runtime, then freezes those corrected bytes.
python3 scripts/ops03_c2_patch_api06.py "$ROOT" | tee "$RUNNER_TEMP/ops03-c2-api06-patch.log"
grep -q '^OPS03_C2_API06_PATCH:PASS:' "$RUNNER_TEMP/ops03-c2-api06-patch.log"
python3 scripts/ops03_c2_harden_g05.py "$ROOT" "$MAIN" "$TREE" | tee "$RUNNER_TEMP/ops03-c2-g05-harden.log"
grep -q '^OPS03_C2_G05_HARDEN:PASS:' "$RUNNER_TEMP/ops03-c2-g05-harden.log"
uvx --from ruff==0.15.22 ruff format \
  "$ROOT/packages/python/epd2-qualification/src/epd2_qualification/api06_binding.py" \
  "$ROOT/packages/python/epd2-qualification/src/epd2_qualification/api06_binding_c2.py" \
  "$ROOT/packages/python/epd2-qualification/src/epd2_qualification/preview_minimum.py" \
  "$ROOT/scripts/validation/validate_ops03.py" \
  "$ROOT/tests/ops03/test_ops03_c2_api06_binding.py"
python3 - "$ROOT" <<'PY'
import pathlib, sys
from scripts.ops03_c2_reconcile import build_freeze, write_sha256sums
root = pathlib.Path(sys.argv[1])
freeze = build_freeze(root)
write_sha256sums(root)
print(f"OPS03_C2_RESEAL:PASS:{freeze['file_count']}:{freeze['tree_digest']}")
PY

jq -e --arg m "$MAIN" --arg t "$TREE" '.candidate_role=="C2" and .candidate_self_state=="CANDIDATE_NOT_ACCEPTED" and .self_accepted==false and (.declared_blockers|length)==0 and .api06_state=="ACCEPTED_CLOSED" and .api_layer_state=="CLOSED" and .system_trial_preview_state=="NOT_OPEN" and .entering_main_commit==$m and .entering_main_tree==$t' "$ROOT/OPS03_CANDIDATE_SELF_STATE.json"
jq -e --arg m "$MAIN" --arg t "$TREE" '.base_commit==$m and .base_tree==$t and .accepted_api06_candidate_filename=="EPD2_API06_API_LAYER_COMPLETION_AND_PREVIEW_READINESS_CANDIDATE_0.1_C1.zip" and .accepted_api06_candidate_sha256=="3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c" and .accepted_api06_candidate_size_bytes==44012716 and .accepted_api06_authoritative_run==33629147572 and .accepted_api06_authoritative_job==100243984921 and .api06_state_at_entry=="ACCEPTED_CLOSED" and .api_layer_state_at_entry=="CLOSED"' "$ROOT/docs/ops/OPS-03/OPS03_ENTERING_BASELINE_IDENTITY.json"
jq -e '.stage=="OPS-03" and .dependency=="API-06" and .state=="ACCEPTED_CLOSED" and .candidate_filename=="EPD2_API06_API_LAYER_COMPLETION_AND_PREVIEW_READINESS_CANDIDATE_0.1_C1.zip" and .candidate_sha256=="3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c" and .candidate_size==44012716 and .authoritative_run_id==33629147572 and .authoritative_job_id==100243984921 and .api_layer_state=="CLOSED" and .binding_result=="PASS" and .system_trial_preview_state=="NOT_OPEN"' "$ROOT/validation/ops03/OPS03_API06_ACCEPTED_RUNTIME_BINDING.json"

# OPS-03 may not rewrite current governance/API/CTRL canonical state.
diff -qr "$RUNNER_TEMP/mainroot/docs/roadmap" "$ROOT/docs/roadmap"
diff -qr "$RUNNER_TEMP/mainroot/docs/api/API-06" "$ROOT/docs/api/API-06"
diff -qr "$RUNNER_TEMP/mainroot/docs/ctrl" "$ROOT/docs/ctrl"
cmp --silent "$RUNNER_TEMP/mainroot/Makefile" "$ROOT/Makefile"
echo 'OPS03_C2_CURRENT_CANONICAL_PRESERVATION:PASS'

WF_SHA=$(sha256sum "$ROOT/handoff/OPS-03/templates/C2/ops03-accept.yml" | cut -d' ' -f1)
ZIP="$RUNNER_TEMP/EPD2_OPS03_OPERATIONAL_QUALIFICATION_ALERTING_CAPACITY_AND_RECOVERY_REHEARSAL_CANDIDATE_0.1_C2.zip"
python3 - "$ROOT" "$ZIP" <<'PY'
import pathlib,stat,sys,zipfile
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2])
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.is_symlink():
            continue
        rel=p.relative_to(root).as_posix()
        if rel.startswith(('.venv/','.git/','.pytest_cache/','.ruff_cache/','.mypy_cache/')) or '/__pycache__/' in f'/{rel}' or rel.endswith('.pyc'):
            continue
        i=zipfile.ZipInfo(rel,(2026,9,2,0,0,0))
        i.compress_type=zipfile.ZIP_DEFLATED
        i.external_attr=(stat.S_IMODE(p.stat().st_mode)&0xffff)<<16
        z.writestr(i,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
PY
CAND_SHA=$(sha256sum "$ZIP" | cut -d' ' -f1)
CAND_SIZE=$(stat -c%s "$ZIP")
test "$CAND_SIZE" -gt 1000000
echo "OPS03_C2_SEALED:$CAND_SHA:$CAND_SIZE:$WF_SHA:$MAIN:$TREE"

cd "$ROOT"
uv sync --all-groups --frozen
sudo apt-get update >/dev/null
sudo apt-get install --yes postgresql-client >/dev/null
SERVER_NUM=$(psql -h 127.0.0.1 -U postgres -tAc 'show server_version_num')
test "$SERVER_NUM" = '160015'
SERVER=$(psql -h 127.0.0.1 -U postgres -tAc 'show server_version')
echo "OPS03_C2_POSTGRES:PASS:$SERVER"

uv run --frozen ruff format --check packages/python/epd2-qualification tests/ops03 scripts/validation/validate_ops03.py scripts/ops03
uv run --frozen ruff check packages/python/epd2-qualification tests/ops03 scripts/validation/validate_ops03.py scripts/ops03
uv run --frozen mypy packages/python/epd2-qualification/src scripts/validation scripts/ops03
uv run --frozen mypy packages/python/epd2-qualification/tests
uv run --frozen mypy tests/ops03
uv run --frozen pytest -q packages/python/epd2-qualification/tests tests/ops03

echo 'OPS03_C2_STATIC_UNIT:PASS'
uv run --frozen python scripts/validation/validate_ops01.py
uv run --frozen python scripts/validation/validate_ops02.py

echo 'OPS03_C2_PREDECESSOR_REGRESSION:PASS'
uv run --frozen python scripts/validation/validate_ops03.py --repo-root "$PWD" --output-dir "$RUNNER_TEMP/ops03-c2-evidence" | tee "$RUNNER_TEMP/ops03-c2-validator.log"
grep -q '^OPS03_RESULT:PASS:validation/ops03/ops03_acceptance_result.json$' "$RUNNER_TEMP/ops03-c2-validator.log"
jq -e '.verdict=="PASS" and .candidate_self_state=="CANDIDATE_NOT_ACCEPTED" and .result.gates_total==50 and .result.gates_passed==50 and .result.gates_failed==[] and .result.gates_missing==[] and .result.environment_blocked==[] and .result.skipped==[] and .result.not_run==[] and .result.manual_assume_pass==[] and .result.same_governed_source_bytes_after_execution==true' "$RUNNER_TEMP/ops03-c2-evidence/ops03_acceptance_result.json"
jq -e '.verdict=="PASS" and .result.total==24 and .result.detected==24 and .result.undetected==0 and (.result.defects|length)==0' "$RUNNER_TEMP/ops03-c2-evidence/mutation_suite_result.json"

python3 - "$PWD" <<'PY'
import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]); f=json.loads((root/'OPS03_FREEZE_MANIFEST.json').read_text())
bad=[]
for rel,d in f['files'].items():
    p=root/rel
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=d:
        bad.append(rel)
assert not bad,bad[:20]
print('OPS03_C2_SEALED_SOURCE_UNCHANGED:PASS')
PY

# Fail closed if canonical main moved while this exact candidate was being qualified.
cd "$REPO_ROOT"
git fetch --no-tags origin main
test "$(git rev-parse origin/main)" = "$MAIN"
test "$(git rev-parse origin/main^{tree})" = "$TREE"

EVID="$RUNNER_TEMP/ops03-c2-build-evidence"
cp "$RUNNER_TEMP/ops03-c2-reconcile.log" "$RUNNER_TEMP/ops03-c2-api06-patch.log" "$RUNNER_TEMP/ops03-c2-g05-harden.log" "$RUNNER_TEMP/ops03-c2-validator.log" "$EVID/"
cp -a "$RUNNER_TEMP/ops03-c2-evidence/." "$EVID/"
python3 - "$EVID/builder_result.json" "$CAND_SHA" "$CAND_SIZE" "$WF_SHA" "$MAIN" "$TREE" <<'PY'
import json,os,sys
out,sha,size,wf,main,tree=sys.argv[1:]
d={
 'schema':'epd2.ops03.c2.builder-result/1','stage':'OPS-03','candidate_role':'C2','result':'PASS','self_acceptance':False,
 'candidate_sha256':sha,'candidate_size_bytes':int(size),'builder_run_id':int(os.environ['GITHUB_RUN_ID']),'builder_commit':os.environ['GITHUB_SHA'],
 'entering_main_commit':main,'entering_main_tree':tree,'accepted_ops02_candidate_sha256':'ac3b543b0cb3a8e45f7d973c841769d0b4c6e7af649a54aee034f3e0b6afc125',
 'accepted_api06_candidate_filename':'EPD2_API06_API_LAYER_COMPLETION_AND_PREVIEW_READINESS_CANDIDATE_0.1_C1.zip',
 'accepted_api06_candidate_sha256':'3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c',
 'accepted_api06_candidate_size_bytes':44012716,'accepted_api06_authoritative_run_id':33629147572,'accepted_api06_authoritative_job_id':100243984921,
 'governed_gates':'50/50 PASS','mutations':'24/24 DETECTED','sealed_source_unchanged':True,'sealed_workflow_sha256':wf,
 'candidate_self_state':'CANDIDATE_NOT_ACCEPTED','system_trial_preview_state':'NOT_OPEN'
}
open(out,'w').write(json.dumps(d,indent=2,sort_keys=True)+'\n')
PY
jq -e '.result=="PASS" and .self_acceptance==false and .candidate_self_state=="CANDIDATE_NOT_ACCEPTED" and .governed_gates=="50/50 PASS" and .mutations=="24/24 DETECTED" and .sealed_source_unchanged==true and .system_trial_preview_state=="NOT_OPEN"' "$EVID/builder_result.json"

{
 echo "candidate=$ZIP"
 echo "candidate_sha=$CAND_SHA"
 echo "candidate_size=$CAND_SIZE"
 echo "workflow_sha=$WF_SHA"
 echo "main=$MAIN"
 echo "tree=$TREE"
 echo "evidence=$EVID"
} >> "$GITHUB_OUTPUT"

echo "OPS03_C2_BUILD_RESULT:PASS:$CAND_SHA:$CAND_SIZE:$WF_SHA:$MAIN:$TREE"