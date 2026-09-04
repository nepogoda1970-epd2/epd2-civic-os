#!/usr/bin/env python3
import argparse, base64, hashlib, io, lzma, pathlib, tarfile, zipfile
EXPECTED_SHA256 = '84e853474a6b62eaddcee742a1d6d7ac28d7879e0261c70af7f053731949991c'
PREDECESSOR_PATHS = ('.github/workflows/infra01-acceptance.yml', '.github/workflows/pilot-roadmap-guard.yml', 'CHANGELOG.md', 'docs/infra/INFRA-01/INFRA-01-ACCEPTANCE-MATRIX.md', 'docs/infra/INFRA-01/INFRA-01-C1-CORRECTION-REPORT.md', 'docs/infra/INFRA-01/INFRA-01-C2-CORRECTION-REPORT.md', 'docs/infra/INFRA-01/INFRA-01-C3-CORRECTION-REPORT.md', 'docs/infra/INFRA-01/INFRA-01-FILE-INVENTORY.md', 'docs/infra/INFRA-01/INFRA-01-FIR-COVERAGE-MATRIX.md', 'docs/infra/INFRA-01/INFRA-01-IMPLEMENTATION-REPORT.md', 'docs/infra/INFRA-01/INFRA-01-KNOWN-LIMITATIONS.md', 'docs/infra/INFRA-01/INFRA01_C0_TO_C2_EXACT_INVENTORY.json', 'docs/infra/INFRA-01/INFRA01_C0_TO_C3_EXACT_INVENTORY.json', 'docs/infra/INFRA-01/INFRA01_C1_TO_C2_EXACT_INVENTORY.json', 'docs/infra/INFRA-01/INFRA01_C2_TO_C3_EXACT_INVENTORY.json', 'docs/infra/INFRA-01/examples/deployment-manifest.example.json', 'docs/infra/INFRA-01/examples/readiness-contract.example.json', 'docs/infra/INFRA-02/INFRA-02-ACCEPTANCE-MATRIX.md', 'docs/infra/INFRA-02/INFRA-02-FILE-INVENTORY.md', 'docs/infra/INFRA-02/INFRA-02-FIR-COVERAGE-MATRIX.md', 'docs/infra/INFRA-02/INFRA-02-IMPLEMENTATION-REPORT.md', 'docs/infra/INFRA-02/INFRA-02-KNOWN-LIMITATIONS.md', 'docs/infra/INFRA-02/INFRA-02-STAGE-CONTRACT.md', 'docs/infra/INFRA-02/INFRA01_C3_TO_INFRA02_EXACT_INVENTORY.json', 'docs/infra/INFRA-02/INFRA02_GOVERNANCE_RECONCILIATION.json', 'scripts/acceptance/__init__.py', 'scripts/acceptance/boundaries.py', 'scripts/acceptance/canonical.py', 'scripts/acceptance/check_registry.json', 'scripts/acceptance/codes.py', 'scripts/acceptance/delta.py', 'scripts/acceptance/deployment_manifest.py', 'scripts/acceptance/evidence.py', 'scripts/acceptance/executor.py', 'scripts/acceptance/freeze.py', 'scripts/acceptance/frozen.py', 'scripts/acceptance/frozen_artifacts.json', 'scripts/acceptance/governance.py', 'scripts/acceptance/hygiene.py', 'scripts/acceptance/identity.py', 'scripts/acceptance/package.py', 'scripts/acceptance/packaging_allowlist.json', 'scripts/acceptance/readiness.py', 'scripts/acceptance/registry.py', 'scripts/acceptance/schemas/check_registry.schema.json', 'scripts/acceptance/schemas/deployment_manifest.schema.json', 'scripts/acceptance/schemas/execution_manifest.schema.json', 'scripts/acceptance/schemas/readiness_contract.schema.json', 'scripts/acceptance/secrets_scan.py', 'scripts/infra02/__init__.py', 'scripts/infra02/ci_policy.py', 'scripts/infra02/codes.py', 'scripts/infra02/dependencies.py', 'scripts/infra02/history_scan.py', 'scripts/infra02/promotion.py', 'scripts/infra02/provenance.py', 'scripts/infra02/release.py', 'scripts/infra02/sbom.py', 'scripts/infra02/schemas/build_provenance.schema.json', 'scripts/infra02/schemas/promotion_record.schema.json', 'scripts/infra02/schemas/release_manifest.schema.json', 'scripts/infra02/schemas/supply_chain_policy.schema.json', 'scripts/infra02/schemas/vulnerability_exceptions.schema.json', 'scripts/infra02/stage.py', 'scripts/infra02/vulnerability.py', 'scripts/infra02/vulnerability_exceptions.json', 'tests/repository/test_infra01_harness_units.py', 'tests/repository/test_infra01_mutation_suite.py', 'tests/repository/test_infra02_mutation_suite.py', 'tests/repository/test_infra02_units.py')
PART_GLOB = 'payload.b64.*'
def safe_dest(root, name):
    name=name.replace('\\','/')
    if name.startswith('/') or name.startswith('../') or '/../' in '/'+name: raise SystemExit(f'unsafe path: {name}')
    dest=(root/name).resolve(); rr=root.resolve()
    if rr != dest and rr not in dest.parents: raise SystemExit(f'escape: {name}')
    return dest
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=pathlib.Path,required=True); ap.add_argument('--predecessor',type=pathlib.Path,required=True); a=ap.parse_args()
    root=a.root.resolve(); here=pathlib.Path(__file__).resolve().parent
    with zipfile.ZipFile(a.predecessor) as z:
        files=[n for n in z.namelist() if not n.endswith('/')]; roots={n.split('/',1)[0] for n in files if '/' in n}
        if len(roots)!=1: raise SystemExit(f'predecessor root ambiguity: {roots}')
        prefix=next(iter(roots))+'/'
        for rel in PREDECESSOR_PATHS:
            member=prefix+rel
            if member not in z.namelist(): raise SystemExit(f'predecessor missing: {rel}')
            dest=safe_dest(root,rel); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(z.read(member))
    parts=sorted(here.glob(PART_GLOB))
    if not parts: raise SystemExit('missing transport parts')
    encoded=b''.join(p.read_bytes() for p in parts); packed=base64.b64decode(b''.join(encoded.split()), validate=True)
    got=hashlib.sha256(packed).hexdigest()
    if got!=EXPECTED_SHA256: raise SystemExit(f'transport sha mismatch {got}')
    raw=lzma.decompress(packed)
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
        seen=set(); applied=0
        for m in tf.getmembers():
            name=m.name.replace('\\','/')
            if m.isdir(): continue
            if not m.isfile() or name in seen: raise SystemExit(f'unsafe/duplicate transport member: {name}')
            seen.add(name); dest=safe_dest(root,name); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(tf.extractfile(m).read()); applied+=1
    print(f'INFRA04_C2_PREDECESSOR_RESTORED:PASS:{len(PREDECESSOR_PATHS)}')
    print(f'INFRA04_C2_DELTA_APPLIED:PASS:{applied}:{EXPECTED_SHA256}')
if __name__=='__main__': main()
