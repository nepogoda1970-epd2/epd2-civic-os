from __future__ import annotations

import base64
import hashlib
import json
import lzma
import re
import subprocess
from collections import Counter
from pathlib import Path

REPO = Path.cwd()
MASTER = REPO / 'docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md'
PCR = REPO / 'docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md'
PATCH_B64 = REPO / '.v25build/v23_to_c5.patch.xz.b64'
OUT_JSON = REPO / 'docs/roadmap/EPD2_MASTER_V25_RECONCILIATION.json'

CURRENT_MAIN_COMMIT = '007b5d71cf5a54e417cbd5647a35a57098ead186'
V23_COMMIT = '5d427eba903999f15b6f6a0d9a3de915a30cf666'
EXPECTED_C5_MERGED_SHA256 = '128c1bf2c060cfe1833bd6c211e9c74823137a3c27e53a37813b7b3f1f1bdd90'
C5_ARCHIVE_SHA256 = 'c9cd83116b6045bc12a5104bf85270cb0fb29883166628924314394ca0e8e978'
ACCEPTED_API01_C5_SHA256 = 'cea2fb0e23ee174e802ec1899cf62e570e5c8659a0f31c7e6c3c3955bffa3d27'
V23_MASTER_SHA256 = '502ddd3ed8c3bf55e3847145772b0863ded01fdcd8521f4c3debf857d0cc0503'

OSS_MARKER = '## V24 governance maintenance record — Open Trust Core & Commercial Operations Boundary (2026-08-29)'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fir_ids(text: str) -> list[str]:
    return re.findall(r'^##\s+(FIR-[A-Z0-9_*.-]+)\b', text, flags=re.M)


def assert_unique(ids: list[str], label: str) -> None:
    dup = sorted(k for k, n in Counter(ids).items() if n > 1)
    if dup:
        raise SystemExit(f'{label}: duplicate FIR headings: {dup}')


head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
if head != CURRENT_MAIN_COMMIT:
    raise SystemExit(f'wrong HEAD: {head}; expected {CURRENT_MAIN_COMMIT}')
parent = subprocess.check_output(['git', 'rev-parse', 'HEAD^'], text=True).strip()
if parent != V23_COMMIT:
    raise SystemExit(f'wrong parent: {parent}; expected {V23_COMMIT}')

current_master_bytes = MASTER.read_bytes()
current_pcr_bytes = PCR.read_bytes()
current_master_sha = sha(current_master_bytes)
current_pcr_sha = sha(current_pcr_bytes)
current_master = current_master_bytes.decode('utf-8')
current_pcr = current_pcr_bytes.decode('utf-8')

if 'FIR-OSS-007' not in current_master:
    raise SystemExit('current main Master does not actually contain FIR-OSS-007')
if OSS_MARKER not in current_master:
    raise SystemExit('current main Master is missing the exact V24 FIR-OSS-007 maintenance marker')

v23_bytes = subprocess.check_output(['git', 'show', f'{V23_COMMIT}:docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md'])
if sha(v23_bytes) != V23_MASTER_SHA256:
    raise SystemExit('V23 Master SHA mismatch')

patch_bytes = lzma.decompress(base64.b64decode(PATCH_B64.read_bytes()))
tmp = Path('/tmp/epd2-v25-build')
tmp.mkdir(exist_ok=True)
v23_path = tmp / 'v23_master.md'
patch_path = tmp / 'v23_to_c5.patch'
c5_path = tmp / 'c5_merged_master.md'
v23_path.write_bytes(v23_bytes)
patch_path.write_bytes(patch_bytes)
subprocess.run(['patch', '-s', '-o', str(c5_path), str(v23_path), str(patch_path)], check=True)
c5_bytes = c5_path.read_bytes()
if sha(c5_bytes) != EXPECTED_C5_MERGED_SHA256:
    raise SystemExit(f'C5 merged reconstruction SHA mismatch: {sha(c5_bytes)}')
c5_master = c5_bytes.decode('utf-8')

oss_block = current_master[current_master.index(OSS_MARKER):].rstrip() + '\n'
if '## FIR-OSS-007' not in oss_block:
    raise SystemExit('FIR-OSS-007 is announced but absent from current-main Master block')
if 'FIR-OSS-007' in c5_master:
    raise SystemExit('C5 merged input unexpectedly already contains FIR-OSS-007')

lines = c5_master.splitlines()
replaced = False
for i, line in enumerate(lines[:12]):
    if line.startswith('**Maintenance copy:**'):
        lines[i] = (
            '**Maintenance copy:** V25 — canonical lossless lineage reconciliation '
            '(2026-08-29): the independently reviewed accepted-maintenance + V23 union is preserved whole, '
            'the exact current-main V24 `FIR-OSS-007` addition is carried from commit '
            f'`{CURRENT_MAIN_COMMIT}`, and no existing FIR is deleted, downgraded or renumbered by this maintenance repair. '
            'See the V25 governance maintenance record and `docs/roadmap/EPD2_MASTER_V25_RECONCILIATION.json`.'
        )
        replaced = True
        break
if not replaced:
    raise SystemExit('maintenance-copy header not found in C5 merged Master')
merged_base = '\n'.join(lines).rstrip() + '\n\n---\n\n' + oss_block

c5_ids = fir_ids(c5_master)
current_ids = fir_ids(current_master)
merged_ids = fir_ids(merged_base)
assert_unique(c5_ids, 'c5_merged')
assert_unique(current_ids, 'current_main')
assert_unique(merged_ids, 'merged_base')
expected_union = set(c5_ids) | set(current_ids)
missing = sorted(expected_union - set(merged_ids))
extra = sorted(set(merged_ids) - expected_union)
if missing or extra:
    raise SystemExit(f'lossless FIR union failed: missing={missing}, extra={extra}')

v25_record = f'''\n---\n\n## V25 governance maintenance record — Lossless reconciliation of the accepted maintenance lineage with current canonical V24 (2026-08-29)\n\n**Why V25 exists.** API-02 C5 independent review established that the then-current V23/V24 Master line and the Master carried by the accepted API-01 maintenance lineage were divergent: the newer governance line contained V17–V24 additions, while the accepted maintenance line contained FIRs and later repository rounds that the newer line had dropped. A candidate-local merge was not sufficient authority. V25 makes that reconciliation upstream and canonical.\n\n**Inputs measured for this reconciliation:**\n\n- current repository main: `{CURRENT_MAIN_COMMIT}`; parent `{V23_COMMIT}`;\n- exact current-main Master SHA-256 before V25: `{current_master_sha}`;\n- exact current-main PCR SHA-256 before V25: `{current_pcr_sha}`;\n- pristine V23 Master SHA-256: `{V23_MASTER_SHA256}`;\n- independently reviewed C5 merged-Master reconstruction SHA-256: `{EXPECTED_C5_MERGED_SHA256}`;\n- API-02 C5 archive SHA-256: `{C5_ARCHIVE_SHA256}`;\n- accepted API-01 C5 archive SHA-256: `{ACCEPTED_API01_C5_SHA256}`.\n\n**Lossless result.** C5 merged input contains `{len(set(c5_ids))}` unique FIR headings; current-main V24 contains `{len(set(current_ids))}`; their union contains `{len(expected_union)}`. The V25 Master contains that entire union with `missing_after_merge = []` and no duplicate FIR headings. The exact current-main `FIR-OSS-007 — Open Trust Core & Commercial Operations Boundary` block is carried from main rather than reconstructed from task text. The accepted-line FIRs restored by the prior reconciliation remain present.\n\n**Conflict rule.** The previously reviewed C5 merge remains the governed resolution for accepted-line versus V23 content conflicts; V25 adds the exact later current-main V24 material and does not reopen those resolved content choices. No FIR is intentionally deleted, downgraded or renumbered by V25. Any future retirement or downgrade requires its own governed decision.\n\n**Execution state:** unchanged. `API-01 = ACCEPTED / CLOSED`; `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. This maintenance repair accepts or closes no implementation stage, activates no cryptographic provider, changes no voting-domain cryptography, and is **NOT PRODUCTION READY / NOT LEGALLY ACTIVATED**.\n'''

v25_master = merged_base.rstrip() + '\n' + v25_record
v25_master_bytes = v25_master.encode('utf-8')
v25_master_sha = sha(v25_master_bytes)
final_ids = fir_ids(v25_master)
assert_unique(final_ids, 'v25')
if set(final_ids) != expected_union:
    raise SystemExit('final V25 FIR set differs from expected union')
for required in ['FIR-UX-012', 'FIR-UX-013', 'FIR-AI-003', 'FIR-GOV-004', 'FIR-GOV-005', 'FIR-SEC-004', 'FIR-TRUST-002', 'FIR-TRUST-003', 'FIR-OSS-007']:
    if required not in final_ids:
        raise SystemExit(f'required FIR missing from V25: {required}')

MASTER.write_bytes(v25_master_bytes)

pcr = current_pcr
pcr = pcr.replace('**Updated:** 2026-08-27', '**Updated:** 2026-08-29', 1)
master_line_pattern = re.compile(r'^Current Master maintenance level established by project governance work: \*\*V24\*\*.*$', re.M)
new_master_line = (
    'Current Master maintenance level established by project governance work: **V25**, preserving the full accepted maintenance lineage '
    'and all legitimate V17–V24 governance additions, including `FIR-UX-012`, `FIR-UX-013`, `FIR-AI-003`, `FIR-GOV-004`, '
    '`FIR-GOV-005`, `FIR-SEC-004`, `FIR-TRUST-002`, `FIR-TRUST-003`, and `FIR-OSS-007`.'
)
pcr, n = master_line_pattern.subn(new_master_line, pcr, count=1)
if n != 1:
    raise SystemExit(f'expected one current V24 Master line in PCR; replaced {n}')

v24_marker = '**Documentation-only V24 governance update (2026-08-29):**'
start = pcr.find(v24_marker)
if start < 0:
    raise SystemExit('current-main V24 PCR record not found')
end = pcr.find('\n\n', start)
if end < 0:
    raise SystemExit('could not locate end of V24 PCR paragraph')

v25_pcr_record = (
    '\n\n**Governance reconciliation V25 (2026-08-29):** the canonical Master was losslessly reconciled upstream from current '
    f'`main@{CURRENT_MAIN_COMMIT}` and the independently reviewed accepted-maintenance/V23 union. The exact V25 Master SHA-256 is '
    f'`{v25_master_sha}`. The reconciliation preserves every FIR from both lineages, carries `FIR-OSS-007` from current main, '
    'restores the accepted-line FIRs absent from the newer governance line, and records `missing_after_merge = []` in '
    '`docs/roadmap/EPD2_MASTER_V25_RECONCILIATION.json`. No API, INFRA, OPS, CTRL, FRONT, SEC, PILOT or voting stage is accepted '
    'or closed by this governance repair. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; '
    'the V23 cryptographic profile and API-02/API-03 gates remain controlling.'
)
pcr = pcr[:end] + v25_pcr_record + pcr[end:]

if pcr.count('Current Master maintenance level established by project governance work: **V25**') != 1:
    raise SystemExit('PCR does not contain exactly one current V25 Master-level claim')
if pcr.count('**Governance reconciliation V25 (2026-08-29):**') != 1:
    raise SystemExit('PCR does not contain exactly one V25 reconciliation record')
if v25_master_sha not in pcr:
    raise SystemExit('PCR does not carry actual V25 Master SHA')
PCR.write_text(pcr, encoding='utf-8')
v25_pcr_sha = sha(PCR.read_bytes())

recon = {
    'schema': 'EPD2_MASTER_V25_RECONCILIATION/1',
    'status': 'PASS',
    'date': '2026-08-29',
    'purpose': 'lossless upstream reconciliation of current canonical V24 with the accepted maintenance/V23 union discovered during API-02 C5/C6 review',
    'source_lineages': {
        'current_main': {
            'commit': CURRENT_MAIN_COMMIT,
            'parent': V23_COMMIT,
            'master_sha256_before_v25': current_master_sha,
            'pcr_sha256_before_v25': current_pcr_sha,
            'unique_fir_count': len(set(current_ids)),
        },
        'v23': {
            'commit': V23_COMMIT,
            'master_sha256': V23_MASTER_SHA256,
        },
        'independently_reviewed_c5_merge': {
            'api02_c5_archive_sha256': C5_ARCHIVE_SHA256,
            'merged_master_sha256': EXPECTED_C5_MERGED_SHA256,
            'accepted_api01_c5_archive_sha256': ACCEPTED_API01_C5_SHA256,
            'unique_fir_count': len(set(c5_ids)),
        },
    },
    'result': {
        'maintenance_level': 'V25',
        'master_sha256': v25_master_sha,
        'pcr_sha256': v25_pcr_sha,
        'current_main_unique_firs': len(set(current_ids)),
        'c5_merged_unique_firs': len(set(c5_ids)),
        'union_unique_firs': len(expected_union),
        'v25_unique_firs': len(set(final_ids)),
        'added_from_current_main_vs_c5_merge': sorted(set(current_ids) - set(c5_ids)),
        'carried_only_from_c5_merge_vs_current_main': sorted(set(c5_ids) - set(current_ids)),
        'missing_after_merge': sorted(expected_union - set(final_ids)),
        'extra_after_merge': sorted(set(final_ids) - expected_union),
        'duplicate_active_ids': sorted(k for k, n in Counter(final_ids).items() if n > 1),
        'required_presence': {k: (k in set(final_ids)) for k in [
            'FIR-UX-012', 'FIR-UX-013', 'FIR-AI-003', 'FIR-GOV-004', 'FIR-GOV-005',
            'FIR-SEC-004', 'FIR-TRUST-002', 'FIR-TRUST-003', 'FIR-OSS-007'
        ]},
    },
    'execution_state_changed': False,
    'acceptance_or_closure_changed': False,
}
OUT_JSON.write_text(json.dumps(recon, indent=2, sort_keys=True) + '\n', encoding='utf-8')

if recon['result']['missing_after_merge'] or recon['result']['duplicate_active_ids']:
    raise SystemExit('V25 reconciliation invariant failed')
if not all(recon['result']['required_presence'].values()):
    raise SystemExit('required FIR presence invariant failed')

print('V25_MASTER_SHA256=' + v25_master_sha)
print('V25_PCR_SHA256=' + v25_pcr_sha)
print('CURRENT_MAIN_MASTER_SHA256=' + current_master_sha)
print('CURRENT_MAIN_PCR_SHA256=' + current_pcr_sha)
print('V25_FIR_COUNT=' + str(len(set(final_ids))))
print('V25_RECONCILIATION=PASS')
