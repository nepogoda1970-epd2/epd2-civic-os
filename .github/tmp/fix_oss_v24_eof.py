from pathlib import Path
import hashlib
import re

master_path = Path('docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md')
control_path = Path('docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md')

master = master_path.read_text(encoding='utf-8').rstrip() + '\n'
master_path.write_text(master, encoding='utf-8')
master_sha = hashlib.sha256(master.encode('utf-8')).hexdigest()

control = control_path.read_text(encoding='utf-8')
marker = '**Documentation-only V24 governance update (2026-08-29):**'
start = control.find(marker)
if start < 0:
    raise SystemExit('V24 Program Control note missing')
end_marker = '**API-02 execution-state reconciliation (2026-08-27):**'
end = control.find(end_marker, start)
if end < 0:
    raise SystemExit('API-02 marker missing after V24 note')
segment = control[start:end]
segment2, count = re.subn(
    r'Canonical Master SHA-256 after this update: `[0-9a-f]{64}`',
    f'Canonical Master SHA-256 after this update: `{master_sha}`',
    segment,
    count=1,
)
if count != 1:
    raise SystemExit('V24 Master hash field missing or ambiguous')
control = control[:start] + segment2 + control[end:]
control_path.write_text(control, encoding='utf-8')

print('NORMALIZED_MASTER_SHA256', master_sha)
