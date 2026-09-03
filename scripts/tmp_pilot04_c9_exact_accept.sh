#!/usr/bin/env bash
set -euo pipefail

PGPASSWORD=postgres psql "$EPD2_TEST_DATABASE_URL" -Atc 'SHOW server_version' | tee "$RUNNER_TEMP/pg.txt"
grep -Fx '16.15' "$RUNNER_TEMP/pg.txt"

echo '5a7ac1f69dffcd5e785461fe02260664e5b9259af9857e6b9c463896a4d65bf8  PILOT04_C8_00.part' | sha256sum -c -
echo 'c5e5b2090fa3dd1b753264455665b5bb49ad743cd8272b697b27175ac0210845  PILOT04_C8_01.part' | sha256sum -c -
echo 'df56b22c7d522e10652f060d925662ce6e1b3fc47252cf2644c4175706fa1b73  PILOT04_C9_00.part' | sha256sum -c -
echo '27f3a7ae239ad9c3638ace3df6e3340dc263f4ea528ff10e17cbe715564b0d30  PILOT04_C9_01.part' | sha256sum -c -

mkdir -p inputs anchors "$RUNNER_TEMP/d"
C8=inputs/EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C8.zip
C9=inputs/EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C9.zip
cat PILOT04_C8_00.part PILOT04_C8_01.part > "$C8"
cat PILOT04_C9_00.part PILOT04_C9_01.part > "$C9"
echo 'd3f7ab7c7fbf87591bf476f21a56b19148fdb400cd6454c12df2377f40938446  '"$C8" | sha256sum -c -
echo '7fc4f3a5a982d11535006fcea8201ffb694546a01f5326eaed09fcf4ffc78664  '"$C9" | sha256sum -c -

P0=artifacts/EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C4.zip.part00
P1=artifacts/EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C4.zip.part01
DB=artifacts/PILOT04_C7_GITHUB_DELTA_BUNDLE.zip
echo '8f750c7821462bbeef50686089353f62d5935f0669bede5e3e166e75f49aa201  '"$P0" | sha256sum -c -
echo '074d33a0eb13ddba1ec54f5dd91d3c4586768c1cb24504ae8d836f5ade78749e  '"$P1" | sha256sum -c -
echo '36cf6781d79394034c4047cff0e9a72abb6cbc14d3df19e4e99a7b2fc81b3c0a  '"$DB" | sha256sum -c -
cat "$P0" "$P1" > inputs/C4.zip
unzip -q "$DB" -d "$RUNNER_TEMP/d"
python scripts/tmp_apply_zip_sparse_patch.py inputs/C4.zip "$RUNNER_TEMP/d/c4_to_pilot04c3.zsp" inputs/C3.zip
python scripts/tmp_apply_zip_sparse_patch.py inputs/C4.zip "$RUNNER_TEMP/d/c4_to_pilot03c3.zsp" anchors/P3.zip
python scripts/tmp_apply_zip_sparse_patch.py inputs/C4.zip "$RUNNER_TEMP/d/c4_to_c5.zsp" inputs/C5.zip
python scripts/tmp_apply_zip_sparse_patch.py inputs/C5.zip "$RUNNER_TEMP/d/c5_to_c6.zsp" inputs/C6.zip
python scripts/tmp_apply_zip_sparse_patch.py inputs/C6.zip "$RUNNER_TEMP/d/c6_to_c7.zsp" inputs/C7.zip

echo '7d9dc40c6b935d2ca899e9c53cc5a1cddef202bc69aa23994871dab1dfa5c1ff  inputs/C3.zip' | sha256sum -c -
echo '994f97c022e499b9847e8c36b48e04aa30b0da0b6e3b4741df13b8f1fcd083d1  inputs/C4.zip' | sha256sum -c -
echo '6d63b8a05e369960e4ef2f691cf4cfb44cf2eae37ffa7cab9fa95064e214b495  inputs/C5.zip' | sha256sum -c -
echo '4899c29a004112d38a33fce51e4e637ceb0951b49a47de71bac5b850e8f31b84  inputs/C6.zip' | sha256sum -c -
echo '812652950e996bd7c781512e4bbc03488c58eb74ca0c652c2b830056d76c1f1d  inputs/C7.zip' | sha256sum -c -
echo '52b5bbfe312d90d65f500f0b6085d33ffe3235ce4bd90562110a26a8fae208d1  anchors/P3.zip' | sha256sum -c -

python - <<'PY'
import hashlib, shutil
from pathlib import Path
exp='442b83d9639a7398b3da767beb95976d379190229610d9b5ccb550d53d277d25'
m=[p for p in Path('pb01').rglob('*') if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==exp]
assert len(m)==1, m
shutil.copyfile(m[0], 'anchors/PB01.zip')
PY

echo '442b83d9639a7398b3da767beb95976d379190229610d9b5ccb550d53d277d25  anchors/PB01.zip' | sha256sum -c -
mkdir workspace
unzip -q "$C9" -d workspace
ROOT="$GITHUB_WORKSPACE/workspace/EPD2_PILOT04_NON_BINDING_DIGITAL_VOTE_PILOT_CANDIDATE_0.1_C9"
cd "$ROOT"
uv sync --frozen --all-groups --all-extras
npm ci --no-audit --no-fund
uv run python scripts/verifier_runtime.py --force --json | tee "$RUNNER_TEMP/verifier.json"
export EPD2_INDEPENDENT_VERIFIER_EXECUTABLE="$EPD2_LOCAL_CI_HOME/verifier-runtime/bin/epd2-verify"
E="$GITHUB_WORKSPACE/PILOT04_C9_ACCEPTANCE_EVIDENCE.json"
uv run python scripts/validate_pilot04_c9.py \
  --candidate "$GITHUB_WORKSPACE/$C9" \
  --predecessor "$GITHUB_WORKSPACE/$C8" \
  --base "$GITHUB_WORKSPACE/inputs/C3.zip" \
  --historical "$GITHUB_WORKSPACE/inputs/C4.zip" --historical "$GITHUB_WORKSPACE/inputs/C5.zip" \
  --historical "$GITHUB_WORKSPACE/inputs/C6.zip" --historical "$GITHUB_WORKSPACE/inputs/C7.zip" \
  --anchor "$GITHUB_WORKSPACE/anchors/P3.zip" --anchor "$GITHUB_WORKSPACE/anchors/PB01.zip" \
  --run-id "github-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}-${GITHUB_SHA}" --json "$E" \
  2>&1 | tee "$GITHUB_WORKSPACE/PILOT04_C9_AUTHORITATIVE.log"
NONCE=$(python -c "import json;d=json.load(open('$E'));print(d['freshness']['nonce'])")
DIGEST=$(python -c "import json;d=json.load(open('$E'));print(d['result_digest'])")
uv run python scripts/validate_pilot04_c9.py --verify "$E" --expect-nonce "$NONCE" --expect-digest "$DIGEST" --require-github-authoritative --max-age 21600
python - <<'PY'
import json, os
d=json.load(open(os.environ['GITHUB_WORKSPACE']+'/PILOT04_C9_ACCEPTANCE_EVIDENCE.json'))
assert d['status']=='PASS' and d['exit_code']==0 and d['all_passed'] is True
assert d['identity']['candidate']['measured_sha256']=='7fc4f3a5a982d11535006fcea8201ffb694546a01f5326eaed09fcf4ffc78664'
assert d['acceptance']['state']=='GITHUB_AUTHORITATIVE_PASS'
assert d['acceptance']['execution']['github_run_id']==os.environ['GITHUB_RUN_ID']
assert d['acceptance']['frozen_acceptance_record']=='NOT_ISSUED'
print('C9_GITHUB_AUTHORITATIVE_PASS')
print('result_digest', d['result_digest'])
print('nonce', d['freshness']['nonce'])
PY
