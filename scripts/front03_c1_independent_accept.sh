#!/usr/bin/env bash
set -euo pipefail

CANDIDATE_RUN_ID=33527376449
CANDIDATE_ARTIFACT=front03-c1-candidate
CANDIDATE_NAME=EPD2_FRONT03_WS02_APPLICANT_AND_MEMBER_CORE_CANDIDATE_0.1_C1.zip
CANDIDATE_SHA256=fec7b19d77c27cbc3ef8a34e433f5aef94ef7853f76d3212bed6acd682497c26
CANDIDATE_SIZE=17646011
API02_RUN_ID=33495990810
API02_ARTIFACT=api02-candidate
API02_NAME=EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C13.zip
API02_SHA256=9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9
API02_SIZE=34642386
API02_ACCEPTANCE_RUN_ID=33497989489
PRESEAL_SHA256=da356d58192fa3afd5cedf0c7d8423df1faac3dd915d5ba26884dcb79e366294
RUNTIME_PROOF_RUN_ID=33526403812
FINALIZE_RUN_ID=33527376449
FINALIZE_JOB_ID=99921554491

: "${GH_TOKEN:?GH_TOKEN required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY required}"
: "${GITHUB_RUN_ID:?GITHUB_RUN_ID required}"
: "${GITHUB_SHA:?GITHUB_SHA required}"

ROOT="$RUNNER_TEMP/front03-c1-independent-accept"
rm -rf "$ROOT"
mkdir -p "$ROOT/incoming/candidate" "$ROOT/incoming/api02" "$ROOT/tree" "$ROOT/api02-tree" "$GITHUB_WORKSPACE/acceptance"

artifact_id() {
  local run_id="$1" name="$2"
  curl -fsSL -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' \
    "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/runs/$run_id/artifacts?per_page=100" \
    | jq -r --arg n "$name" '[.artifacts[] | select(.name==$n and .expired==false)] | if length==1 then .[0].id else error("artifact identity not unique") end'
}

download_artifact() {
  local run_id="$1" name="$2" dest="$3" id zip
  id="$(artifact_id "$run_id" "$name")"
  zip="$ROOT/$name.artifact.zip"
  curl -fL --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' \
    "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$id/zip" -o "$zip"
  unzip -q "$zip" -d "$dest"
  echo "$id"
}

CANDIDATE_ARTIFACT_ID="$(download_artifact "$CANDIDATE_RUN_ID" "$CANDIDATE_ARTIFACT" "$ROOT/incoming/candidate")"
API02_ARTIFACT_ID="$(download_artifact "$API02_RUN_ID" "$API02_ARTIFACT" "$ROOT/incoming/api02")"
ZIP="$ROOT/incoming/candidate/$CANDIDATE_NAME"
API="$ROOT/incoming/api02/$API02_NAME"
test -f "$ZIP"; test -f "$API"
test "$(stat -c %s "$ZIP")" = "$CANDIDATE_SIZE"
test "$(stat -c %s "$API")" = "$API02_SIZE"
echo "$CANDIDATE_SHA256  $ZIP" | sha256sum -c -
echo "$API02_SHA256  $API" | sha256sum -c -
unzip -t "$ZIP" >/dev/null
unzip -t "$API" >/dev/null

RUN_JSON="$(curl -fsSL -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/runs/$FINALIZE_RUN_ID")"
jq -e '.id == 33527376449 and .conclusion == "success" and .name == "FRONT-03 C1 governed finalize"' <<<"$RUN_JSON" >/dev/null
JOBS_JSON="$(curl -fsSL -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/runs/$FINALIZE_RUN_ID/jobs?per_page=100")"
jq -e --argjson jid "$FINALIZE_JOB_ID" '.jobs[] | select(.id==$jid) | .conclusion=="success"' <<<"$JOBS_JSON" >/dev/null

unzip -q "$ZIP" -d "$ROOT/tree"
unzip -q "$API" -d "$ROOT/api02-tree"
API_ROOT="$(find "$ROOT/api02-tree" -mindepth 1 -maxdepth 1 -type d -name 'EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C13' -print -quit)"
test -n "$API_ROOT"
cd "$ROOT/tree"

python3 - <<'PY'
import json,re
from pathlib import Path
r=Path('.')
b=json.loads((r/'docs/frontend/FRONT-03-C1-API02-CONTRACT-BINDINGS.json').read_text())
e=json.loads((r/'validation/front03-c1/execution.json').read_text())
assert b['candidate_state']=='C1_CANDIDATE_NOT_ACCEPTED'
assert b['api03_dependency']=='NONE_DISCOVERED_FOR_C1_BROWSER_TO_API02_BINDING'
assert e['status']=='PASS' and e['candidate_state']=='CANDIDATE_NOT_ACCEPTED'
assert e['runtime_proof_run_id']==33526403812
assert e['accepted_api02_sha256']=='9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9'
texts='\n'.join(p.read_text(errors='ignore') for p in r.rglob('*') if p.is_file() and p.suffix in {'.md','.json','.ts','.tsx','.py','.csv'})
assert not re.search(r'FRONT-03\s*=\s*(ACCEPTED|CLOSED)|FRONT-03\s+(ACCEPTED|CLOSED)',texts,re.I)
PY

npm ci
npm run --workspace=frontend/web-shell format:check
npm run typecheck --workspace=frontend/web-shell
npm run lint --workspace=frontend/web-shell
npm run test --workspace=frontend/web-shell
npm run build --workspace=frontend/web-shell

export FRONT03_TEST_PROFILE=fixture NEXT_PUBLIC_FRONT03_FIXTURE=1 EPD2_FRONT03_GOVERNED_TEST_CONTEXT=1
npm exec --workspace web-shell playwright test -- tests/browser/front00.browser.spec.ts --grep-invert '@visual'
npm exec --workspace web-shell playwright test -- tests/browser/front01.browser.spec.ts --grep-invert '@front01-visual'
npm exec --workspace web-shell playwright test -- tests/browser/front02.browser.spec.ts tests/browser/pack15.browser.spec.ts tests/browser/front03.browser.spec.ts --grep-invert '@visual'

export NODE_ENV=production FRONT03_TEST_PROFILE=production NEXT_PUBLIC_FRONT03_FIXTURE=0 EPD2_FRONT03_GOVERNED_TEST_CONTEXT=0
npm exec --workspace web-shell playwright test -- tests/browser/front03.c1.browser.spec.ts
npm exec --workspace web-shell playwright test -- tests/browser/front03.production.browser.spec.ts

unset NODE_ENV
export FRONT03_TEST_PROFILE=fixture NEXT_PUBLIC_FRONT03_FIXTURE=1 EPD2_FRONT03_GOVERNED_TEST_CONTEXT=1
MANIFEST=frontend/web-shell/tests/browser/front03-r3-visual-baseline.sha256
SNAPDIR=frontend/web-shell/tests/browser/front03.browser.spec.ts-snapshots
test "$(grep -c 'front03-.*\.png$' "$MANIFEST")" -eq 27
test "$(find "$SNAPDIR" -maxdepth 1 -type f -name '*.png' | wc -l)" -eq 27
(cd frontend/web-shell && sha256sum -c tests/browser/front03-r3-visual-baseline.sha256)
BEFORE="$(sha256sum "$MANIFEST" | cut -d' ' -f1)"
npm exec --workspace web-shell playwright test -- tests/browser/front03.browser.spec.ts --grep '@visual'
test "$BEFORE" = "$(sha256sum "$MANIFEST" | cut -d' ' -f1)"
(cd frontend/web-shell && sha256sum -c tests/browser/front03-r3-visual-baseline.sha256)

python3 -m py_compile scripts/validate_front03_c1.py scripts/run_front03_c1_mutations.py
python3 scripts/validate_front03_c1.py . --api02-root "$API_ROOT" | tee "$GITHUB_WORKSPACE/acceptance/front03-c1-accept-validator.json"
python3 scripts/run_front03_c1_mutations.py --root . --api02-root "$API_ROOT" --output "$GITHUB_WORKSPACE/acceptance/front03-c1-accept-mutations.json"
python3 scripts/validate_front03_c1.py . --api02-root "$API_ROOT" > "$GITHUB_WORKSPACE/acceptance/front03-c1-accept-validator-final.json"

python3 - "$CANDIDATE_ARTIFACT_ID" "$API02_ARTIFACT_ID" <<'PY'
import json,os,sys
candidate_artifact_id,api02_artifact_id=map(int,sys.argv[1:])
row={
 'schema':'epd2.front03.c1-acceptance-evidence/1',
 'status':'PASS',
 'decision_scope':'INDEPENDENT_GOVERNED_TECHNICAL_ACCEPTANCE_EVIDENCE',
 'candidate_name':'EPD2_FRONT03_WS02_APPLICANT_AND_MEMBER_CORE_CANDIDATE_0.1_C1.zip',
 'candidate_sha256':'fec7b19d77c27cbc3ef8a34e433f5aef94ef7853f76d3212bed6acd682497c26',
 'candidate_size':17646011,
 'candidate_artifact_id':candidate_artifact_id,
 'acceptance_run_id':int(os.environ['GITHUB_RUN_ID']),
 'acceptance_commit':os.environ['GITHUB_SHA'],
 'finalize_run_id':33527376449,
 'runtime_proof_run_id':33526403812,
 'source_preseal_sha256':'da356d58192fa3afd5cedf0c7d8423df1faac3dd915d5ba26884dcb79e366294',
 'accepted_api02_sha256':'9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9',
 'accepted_api02_acceptance_run_id':33497989489,
 'api02_artifact_id':api02_artifact_id,
 'gates':{
  'exact_bytes_crc':'PASS','fresh_dependencies_compile_unit_build':'PASS','inherited_browser':'PASS',
  'api02_production_browser':'PASS','production_fail_closed':'PASS','immutable_visual_27':'PASS',
  'c1_validator_14':'PASS','c1_mutations_9_of_9':'PASS','no_api03_dependency_discovered':'PASS','no_self_acceptance':'PASS'
 },
 'claim_boundary':'technical acceptance for bounded FRONT-03 stage only; entire FRONT layer remains governed separately'
}
Path=os.path
open(os.path.join(os.environ['GITHUB_WORKSPACE'],'acceptance','FRONT03_C1_ACCEPTANCE_EVIDENCE.json'),'w').write(json.dumps(row,indent=2,sort_keys=True)+'\n')
PY

echo "FRONT03_C1_ACCEPTANCE_RESULT:PASS:$CANDIDATE_SHA256:$CANDIDATE_SIZE"
