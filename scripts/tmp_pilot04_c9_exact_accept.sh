#!/usr/bin/env bash
set -euo pipefail

# TEMPORARY BINARY TRANSPORT ONLY.
# This script intentionally exits non-zero after preparing the transport payload.
# It MUST NOT be interpreted as PILOT-04 acceptance evidence.

P0="tmp/PILOT05_C3_00.part"
P1="tmp/PILOT05_C3_01.part"
OUT="/tmp/EPD2_PILOT05_REPRESENTATIVE_DESK_AND_TRANSPARENCY_PILOT_CANDIDATE_0.1_C3.zip"
EXPECTED="fc3f371bcf180e6559bc8ccc72cb74a88deef293f768424bcae7576731e8d8fb"

test -f "$P0"
test -f "$P1"
cat "$P0" "$P1" > "$OUT"
ACTUAL="$(sha256sum "$OUT" | awk '{print $1}')"
if [[ "$ACTUAL" != "$EXPECTED" ]]; then
  echo "TRANSPORT_SHA_MISMATCH expected=$EXPECTED actual=$ACTUAL" >&2
  exit 97
fi

python3 - "$OUT" <<'PY'
import sys, zipfile
p=sys.argv[1]
with zipfile.ZipFile(p) as z:
    bad=z.testzip()
    if bad is not None:
        raise SystemExit(f"CRC_FAIL:{bad}")
    names=z.namelist()
    roots={n.split('/',1)[0] for n in names if n and not n.startswith('/')}
    if len(names) != 3744:
        raise SystemExit(f"MEMBER_COUNT_FAIL:{len(names)}")
    expected={'EPD2_PILOT05_REPRESENTATIVE_DESK_AND_TRANSPARENCY_PILOT_CANDIDATE_0.1_C3'}
    if roots != expected:
        raise SystemExit(f"ROOT_FAIL:{roots}")
PY

cat > PILOT04_C9_ACCEPTANCE_EVIDENCE.json <<EOF
{
  "transport_only": true,
  "acceptance_evidence": false,
  "purpose": "recover exact immutable PILOT-05 C3 bytes from accepted transport blobs",
  "pilot05_c3_sha256": "$ACTUAL",
  "pilot05_authoritative_run_id": 32855264419,
  "notice": "NOT PILOT-04 EVIDENCE; DO NOT USE FOR ANY PASS OR ACCEPTANCE CLAIM"
}
EOF

{
  echo 'EPD2_TEMP_TRANSPORT_V1'
  echo 'NOT_ACCEPTANCE_EVIDENCE'
  echo "SHA256=$ACTUAL"
  echo 'BASE64_BEGIN'
  base64 -w 0 "$OUT"
  echo
  echo 'BASE64_END'
} > PILOT04_C9_AUTHORITATIVE.log

echo "TRANSPORT_READY sha256=$ACTUAL bytes=$(stat -c %s "$OUT")"
echo "INTENTIONAL_FAILURE_AFTER_TRANSPORT_PREPARATION" >&2
exit 42
