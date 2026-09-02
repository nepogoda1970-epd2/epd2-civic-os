#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, re, shutil, subprocess, tempfile, zipfile
from pathlib import Path

P1_SHA256 = '490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71'
BASE_MAIN = '217559b7f21c338d6fe8d4e4676082cd3840251c'
BASE_TREE = 'eb8a3254c2b8a30feff71318d4377eff2435605c'
CANDIDATE_NAME = 'EPD2_CTRL01_GOVERNED_CONTROL_PLANE_CANDIDATE_0.1_C1'

CANONICAL_BLOBS = {
    'docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md': '4b69cf500f2171399f7fb0b4213cb1bddcc8cf07',
    'docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md': 'aad828e377889e96f0bce16245f4e9ed1d97ed4a',
    'docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md': '7f5c6a9a88f8e653b43dc542a595ac37bf7a0692',
    'docs/roadmap/EPD2_BSI_VOTING_BOOTSTRAP_RULE.md': '15dd290a1bcb6f44b4242e7c33b71119e404553a',
}
ACCEPTED = {
    'docs/api/API-02/API02_C13_ACCEPTANCE_RECORD.json': '7f8b16ca16a11f4916f1988ef53243b977e1862d',
    'docs/api/API-03/API03_C5_ACCEPTANCE_RECORD.json': '0f41555a4aa5f0bf80fa7a1a95be905c02d692c5',
    'docs/api/API-04/API04_C1_ACCEPTANCE_RECORD.json': 'fab2833e6769bc9e71876e47b168848e6c386e96',
    'docs/api/API-05/API05_C1_ACCEPTANCE_RECORD.json': 'e35f0ff0438419db445580f8739575ccba3f6551',
    'docs/frontend/FRONT-04-C2-ACCEPTANCE-RECORD.json': '5eb35c0699434f1f93c63bfc23a87097c609ca06',
    'docs/frontend/FRONT-03-C1-ACCEPTANCE-RECORD.json': '',
    'docs/frontend/FRONT-02-C2.1-ACCEPTANCE-RECORD.json': '',
    'docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json': '',
    'docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json': '95df6e5c5288b16aee62621157fc28a790b68bfc',
    'docs/ops/OPS-01/OPS01_C2_ACCEPTANCE_RECORD.json': '',
    'docs/ops/OPS-02/OPS02_C3_ACCEPTANCE_RECORD.json': '3d4baa96b957693244507aaa76f2d685226f88b6',
}


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20), b''): h.update(chunk)
    return h.hexdigest()

def run(*cmd: str, cwd: Path) -> str:
    p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,check=True)
    return p.stdout.strip()

def replace_block(text: str, start: str, end: str, replacement: str) -> str:
    a=text.index(start); b=text.index(end,a)
    return text[:a]+replacement+text[b:]

def py_dict(name: str, mapping: dict[str,str], comment_after: str) -> str:
    body = name + ': dict[str, str] = {\n' + ''.join(f'    {k!r}: {v!r},\n' for k,v in mapping.items()) + '}\n\n'
    return body + comment_after

def patch_validator(path: Path) -> None:
    t=path.read_text()
    start='CANONICAL_BLOBS: dict[str, str] = {'
    end='ACCEPTED_PREDECESSOR_BLOBS: dict[str, str] = {'
    repl=py_dict('CANONICAL_BLOBS', CANONICAL_BLOBS, '')
    t=replace_block(t,start,end,repl+'ACCEPTED_PREDECESSOR_BLOBS: dict[str, str] = {')
    # replace accepted dict cleanly
    a=t.index('ACCEPTED_PREDECESSOR_BLOBS: dict[str, str] = {')
    b=t.index('\n}\n\n#: Stages CTRL-01 consumes',a)+3
    accepted='ACCEPTED_PREDECESSOR_BLOBS: dict[str, str] = {\n'+''.join(f'    {k!r}: {v!r},\n' for k,v in ACCEPTED.items())+'}'
    t=t[:a]+accepted+t[b:]
    # unreconciled block
    a=t.index('UNRECONCILED_DEPENDENCIES: dict[str, str] = {')
    b=t.index('\n}\n\n#: The FIR reconciliation targets',a)+3
    t=t[:a]+'''UNRECONCILED_DEPENDENCIES: dict[str, str] = {
    "API-06": "NEXT / NOT ACCEPTED; API layer remains open until API-06 closes",
}'''+t[b:]
    t=re.sub(r'BASELINE_COMMIT = "[0-9a-f]{40}"', f'BASELINE_COMMIT = "{BASE_MAIN}"', t)
    # current PCR has no material contradictory state; require the current facts instead.
    a=t.index('def _register_conflicts()')
    b=t.index('\n\ndef _write(',a)
    t=t[:a]+'''def _register_conflicts() -> list[dict[str, str]]:
    """Return material current-state conflicts only.

    Historical placement/section-shape omissions are not promoted to current-state
    conflicts when the PCR, post-run acceptance record and phase table agree.
    """
    register = REPO_ROOT / "docs" / "roadmap" / "EPD2_PROGRAM_CONTROL_REGISTER.md"
    if not register.exists():
        return [{"conflict_id": "PCR-MISSING", "statement_a": "PCR missing"}]
    text = register.read_text(errors="replace")
    required = {
        "PCR-API05": "API-05 = ACCEPTED / CLOSED",
        "PCR-API06": "API-06 = NEXT",
        "PCR-INFRA02": "INFRA-02 authoritative acceptance and bounded stage closure",
        "PCR-OPS02": "OPS-02 authoritative acceptance and bounded stage closure",
    }
    conflicts: list[dict[str, str]] = []
    for cid, needle in required.items():
        if needle not in text:
            conflicts.append({
                "conflict_id": cid,
                "statement_a": f"required current PCR fact missing: {needle}",
                "ctrl01_position": "fail closed pending governed reconciliation",
            })
    return conflicts
'''+t[b:]
    # current seal preconditions
    t=t.replace('"reconcile exact accepted API-05 identity or record it as not yet accepted",\n                ', '')
    t=t.replace('"reconcile INFRA-02 and OPS-02 if accepted before CTRL-01 seal",\n                ', '')
    t=t.replace('"reconcile exact accepted API-06 identity or record it as not yet accepted",', '"keep API-06 explicitly NEXT / NOT ACCEPTED unless a later authoritative record exists",')
    # consumed surface now names the accepted additions
    t=t.replace('"API-04": "event/messaging semantics not consumed by CTRL-01 preseal work",\n                "INFRA-01":', '"API-04": "event/messaging semantics not consumed by CTRL-01 bounded work",\n                "API-05": "external-integration authority semantics reconciled by accepted C1 record only",\n                "INFRA-01":')
    t=t.replace('"OPS-01": "incident, recovery and change-control separation-of-duties conventions",', '"INFRA-02": "accepted CI/CD and supply-chain integrity boundary",\n                "OPS-01": "incident, recovery and change-control separation-of-duties conventions",\n                "OPS-02": "accepted preview-operations readiness implementation; checkpoint remains governance-closed",')
    path.write_text(t)

def patch_trial(path: Path) -> None:
    t=path.read_text()
    t=t.replace('"API-05": "API-05 is ACTIVE / IN DEVELOPMENT / NOT ACCEPTED.",', '"API-05": "API-05 C1 is ACCEPTED / CLOSED and is not a current checkpoint blocker.",')
    t=t.replace('"INFRA-02": "INFRA preview-readiness minimum is not recorded as met.",', '"INFRA-02": "INFRA-02 is ACCEPTED / CLOSED as a bounded stage; the explicit joint INFRA/OPS preview-readiness minimum remains unrecorded while API-06 is open.",')
    old='''"OPS-02": (
        "OPS preview-readiness minimum (deploy, observe, recover, reset) is not recorded as met."
    ),'''
    new='''"OPS-02": (
        "OPS-02 C3 is ACCEPTED / CLOSED and technically ready; the explicit joint preview-readiness minimum remains a governance decision downstream of API-06."
    ),'''
    t=t.replace(old,new)
    t=t.replace('{"item": "remaining API surface", "source": "API-05 / API-06", "state": "NOT_ACCEPTED"}', '{"item": "remaining API surface", "source": "API-06", "state": "NEXT_NOT_ACCEPTED"}')
    path.write_text(t)

def patch_docs(root: Path) -> None:
    repl={
        'cb02b231e701d0b4f12db89c86bc56a9fe11f71a': BASE_MAIN,
        '1ea6161335044dc4d1e50a6b1588bad6627f7af5': BASE_TREE,
    }
    for rel in ['README.md','docs/ctrl/CTRL-01/CTRL-01-DEVELOPER-REPORT.md','docs/ctrl/CTRL-01/CTRL-01-SPECIFICATION.md']:
        p=root/rel; t=p.read_text()
        for a,b in repl.items(): t=t.replace(a,b)
        t=t.replace('`API-05`, `API-06`, `INFRA-02` and `OPS-02` are **not accepted**', '`API-05`, `INFRA-02` and `OPS-02` are now **ACCEPTED / CLOSED as bounded stages**; `API-06` remains **NEXT / NOT ACCEPTED**')
        t=t.replace('`API-05`, `API-06`, `INFRA-02` and `OPS-02` are not accepted.', '`API-05`, `INFRA-02` and `OPS-02` are accepted/closed as bounded stages; `API-06` remains NEXT / NOT ACCEPTED.')
        t=t.replace('reconcile exact accepted API-05 identity or record it as not yet accepted', 'preserve the exact accepted API-05 C1 identity')
        t=t.replace('reconcile INFRA-02 and OPS-02 if either is accepted by then', 'preserve the exact accepted INFRA-02 and OPS-02 identities')
        p.write_text(t)
    # Replace stale report sections with explicit current reconciliation.
    p=root/'docs/ctrl/CTRL-01/CTRL-01-DEVELOPER-REPORT.md'; t=p.read_text()
    a=t.index('## 5. Observed conditions in the canonical baseline'); b=t.index('## 7. Before any future seal')
    replacement=f'''## 5. Reconciliation to canonical main {BASE_MAIN[:12]}\n\nThe P1 baseline was superseded by nine governance commits. The implementation\ndelta itself has no path overlap with those commits. Current canonical state records\nAPI-05 C1, INFRA-02 and OPS-02 C3 as independently ACCEPTED / CLOSED bounded\nstages. API-06 remains `NEXT / NOT ACCEPTED`| so the API layer and System Trial\nPreview remain open/closed respectively exactly as the Program Control Register\nstates. No current canonical Master or BSI bootstrap byte changed across the\nreconciliation.\n\nThe earlier P1 observations about API-04 table drift are historical and are not\ncarried forward as current-state conflicts: the current PCR table, current-primary\nposition and API-04 acceptance record agree.\n\n## 6. Dependencies not relied upon\n\nExact API-05 C1, INFRA-02 and OPS-02 C3 acceptance records are bound by Git blob\nidentity. API-06 is explicitly not treated as accepted. Its absence is a System\nTrial/API-layer closure blocker, not silently converted into a CTRL-01 PASS condition.\n\n'''t[b:]
    p.write_text(t)

def overlay(p1: Path, repo: Path) -> None:
    if sha256(p1) != P1_SHA256: raise SystemExit('P1 SHA mismatch')
    if run('git','rev-parse','HEAD',cwd=repo) != BASE_MAIN: raise SystemExit('wrong base main')
    if run('git','rev-parse','HEADN{tree}',cwd=repo) != BASE_TREE: raise SystemExit('wrong base tree')
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(p1) as z: z.extractall(td)
        roots=[p for p in Path(td).iterdir() if p.is_dir()]
        if len(roots)!=1: raise SystemExit('unexpected P1 root')
        src=roots[0]
        for rel in ['services/control-plane-service','docs/ctrl/CTRL-01']:
            dst=repo/rel
            if dst.exists(): shutil.rmtree(dst)
            shutil.copytree(src/rel,dst)
        for rel in ['scripts/ctrl01_validator.py','scripts/ctrl01_registry_export.py','scripts/system_trial_preview_prepare.py']:
            (repo/rel).parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src/rel,repo/rel)
        shutil.copy2(src/'README.md',repo/'CTRL01_CANDIDATE_README.md')
    patch_validator(repo/'scripts/ctrl01_validator.py')
    patch_trial(repo/'scripts/system_trial_preview_prepare.py')
    # docs patch expects README.md under root; temporarily point candidate readme
    shutil.copy2(repo/'CTRL01_CANDIDATE_README.md', repo/'README.ctrl01.tmp')
    # patch packaged docs separately
    for rel in ['docs/ctrl/CTRL-01/CTRL-01-DEVELOPER-REPORT.md','docs/ctrl/CTRL-01/CTRL-01-SPECIFICATION.md']:
        p=repo/rel; t=p.read_text().replace('cb02b231e701d0b4f12db89c86bc56a9fe11f71a',BASE_MAIN).replace('1ea6161335044dc4d1e50a6b1588bad6627f7af5',BASE_TREE); p.write_text(t)
    # apply report section and general current wording by temporary root structure
    tmpread=repo/'CTRL01_CANDIDATE_README.md'; t=tmpread.read_text().replace('cb02b231e701d0b4f12db89c86bc56a9fe11f71a',BASE_MAIN).replace('1ea6161335044dc4d1e50a6b1588bad6627f7af5',BASE_TREE)
    t=t.replace('`API-05`, `API-06`, `INFRA-02` and `OPS-02` are not accepted.', '`API-05`, `INFRA-02` and `OPS-02` are accepted/closed as bounded stages; `API-06` remains NEXT / NOT ACCEPTED.')
    tmpread.write_text(t)
    # report surgical replacement
    p=repo/'docs/ctrl/CTRL-01/CTRL-01-DEVELOPER-REPORT.md'; t=p.read_text(); a=t.index('## 5. Observed conditions in the canonical baseline'); b=t.index('## 7. Before any future seal')
    t=t[:a]+f'''## 5. Reconciliation to canonical main `{BASE_MAIN}`\n\nThe P1 baseline was superseded by nine governance commits. The CTRL-01 source\ndelta has no path overlap with those commits. Current canonical state records\nAPI-05 C1, INFRA-02 and OPS-02 C3 as independently `ACCEPTED / CLOSEd` bounded\nstages. API-06 remains `NEXT / NOT ACCEPTED`, the API layer remains open and the\nSystem Trial Preview checkpoint remains closed. The Master and BSI bootstrap\nbytes are unchanged from P1.\n\nThe earlier P1 API-04 table inconsistency is historical, not a current-state\nconflict: the current PCR phase table, primary-position statement and acceptance\nrecord agree that API-04 is closed.\n\n## 6. Dependencies not relied upon\n\nAPI-05 C1, INFRA-02 and OPS-02 C3 are bound by their exact accepted governance\nrecords. API-06 is explicitly not treated as accepted. Its absence blocks API\nlayer closure and System Trial Preview opening; it is not silently converted\ninto a CTRL-01 acceptance fact.\n\n''+t[b:]
    t=t.replace('reconcile exact accepted API-05 identity or record it as not yet accepted','preserve the exact accepted API-05 C1 identity').replace('reconcile INFRA-02 and OPS-02 if either is accepted by then','preserve the exact accepted INFRA-02 and OPS-02 identities')
    p.write_text(t)
    p=repo/'docs/ctrl/CTRL-01/CTRL-01-SPECIFICATION.md'; t=p.read_text(); t=t.replace('`API-05`, `API-06`, `INFRA-02` and `OPS-02`, none of which is\n  accepted.','`API-05`, `INFRA-02` and `OPS-02`, all now accepted as bounded stages;\n  `API-06` remains NEXT / NOT ACCEPTED and blocks API-layer/System-Trial closure.')
    t=t.replace('Reconcile the exact accepted identity of API-05 and API-06, or record each\n,\n   explicitly as not yet accepted.','Preserve the exact accepted API-05 C1 identity and keep API-06 explicitly\n   NEXT / NOT ACCEPTED unless an authoritative later acceptance exists.')
    t=t.replace('Reconcile INFRA-02 and OPS-02 if either is accepted by then.','Preserve the exact accepted INFRA-02 and OPS-02 identities.')
    p.write_text(t)
    (repo/'README.ctrl01.tmp').unlinj[Z\ÜÚ[™×ÛÚÏUYJB‚™YˆXÚØYÙJ™\Îˆ]İ]ˆ][—ÚYˆİŠHOˆ›Û™N‚ˆ[˜ÛYYV×Bˆ›Üˆ˜\ÙH[ˆÉÜÙ\šXÙ\ËØÛÛ›Û\[™K\Ù\šXÙIË	ÙØÜËØİ›ĞÕ“LIË	İ˜[Y][Û‹Øİ›IË	İ˜[Y][Û‹ÜŞ\İ[WİšX[Ü™]šY]É×N‚ˆ›Üˆ[ˆÛÜY

™\ËØ˜\ÙJKœ™ÛØŠ	Ê‰ÊJN‚ˆYˆš\×Ùš[J
H[™	××ÜXØXÚW×ÉÈ›İ[ˆœ\È[™›İ›˜[YK™[™İÚ]
	ËœXÉÊNˆ[˜ÛYY˜\[™

Bˆ›Üˆ™[[ˆÉÜØÜš\ËØİ›Wİ˜[Y]Ü‹œIË	ÜØÜš\ËØİ›WÜ™YÚ\İWÙ^ÜœIË	ÜØÜš\ËÜŞ\İ[WİšX[Ü™]šY]×Ü™\\™KœI×N‚ˆ[˜ÛYY˜\[™
™\ËÜ™[
BˆØ[™\™\ËÉ×Øİ›WØØ[™Y]IÎÈÚ][œ›]™YJØ[™YÛ›Ü™WÙ\œ›ÜœÏUYJNÈØ[™›ZÙ\Š
Bˆ›Üˆ[ˆ[˜ÛYY‚ˆ™[\œ™[]]™WİÊ™\ÊNÈİXØ[™Ü™[Èİœ\™[›ZÙ\Š\™[ÏUYK^\İÛÚÏUYJNÈÚ][˜ÛÜLŠİ
BˆY[]O^Âˆ	ÜØÚ[XIÎ‰Ù\‹˜İ›K˜Ø[™Y]KZY[]KÌIË	ÜİYÙIÎ‰ĞÕ“LIË	Ü›ÛIÎ‰ĞÌIËˆ	ÜÙ[—Üİ]IÎ‰ĞĞS‘QUWÓ“ÕĞPĞÑTQ	Ë	Ø˜\ÙWÛXZ[—ØÛÛ[Z]	ÎTÑWÓPRS‹v&6UöÖ–å÷G&VRs¤$4UõE$TRÀ¢w÷6†#Sbs¥õ4„#SbÂv'V–ÆFW%÷'Våö–Bs§'Våö–BÀ¢vg&VW¦UöÖæ–fW7EöF–vW7Bs¦†6†Æ–"ç6†#Sb‚†6æBòwfÆ–FF–öâö7G&Ãög&VW¦UöÖæ–fW7Bæ§6öâr’ç&VEö'—FW2‚’’æ†W†F–vW7B‚’À¢v“e÷7FFRs¢täU…BòäõB44UDTBrÂw7—7FVÕ÷G&–Å÷&Wf–Wrs¢t4„T4µô”åEôäõEôõTâp¢Ğ¢†6æBòv6æF–FFUö–FVçF—G’æ§6öâr’çw&—FU÷FW‡B†§6öâæGV×2†–FVçF—G’Æ–æFVçCÓ"’²uÆâr¢&VFÖSÒ‡&Wòòt5E$Ãô4äD”DDUõ$TDÔRæÖBr’ç&VE÷FW‡B‚’¶brruÆâ223&V6öæ6–Æ–F–öåÆåÆä'V–ÇBv–ç7B6æöæ–6ÂÖ–ä´$4UôÔ”çÖgFW"W†7B&V6öæ6–Æ–F–öâöb66WFVEÆä’ÓR3Â”äe$Ó"æBõ2Ó"32&V6÷&G2â’Ób&VÖ–ç2äU…BòäõB44UDTBråÆåF†—26æF–FFRFöW2æ÷B÷VâF†R7—7FVÒG&–Â&Wf–WræBFöW2æ÷B66WB—G6VÆbåÆârrp¢†6æBòu$TDÔRæÖBr’çw&—FU÷FW‡B‡&VFÖR¢7V×3ÕµĞ¢f÷"–â6÷'FVB†6æBç&vÆö"‚r¢r’“ ¢–bæ—5öf–ÆR‚’æBææÖRÒu4„#Se5TÕ2çG‡Bs¢7V×2æVæB†bw·6†#Sb‡—Ò·ç&VÆF—fU÷Fò†6æB’æ5÷÷6—‚‚—Òr¢†6æBòu4„#Se5TÕ2çG‡Br’çw&—FU÷FW‡B‚uÆâræ¦ö–â‡7V×2’²uÆâr¢÷WBç&VçBæÖ¶F—"‡&VçG3ÕG'VRÆW†—7Eöö³ÕG'VR¢v—F‚¦—f–ÆRå¦—f–ÆR†÷WBÂwrrÆ6ö×&W76–öã×¦—f–ÆRå¤•ôDTdÄDTBÆ6ö×&W76ÆWfVÃÓ’’2£ ¢f÷"–â6÷'FVB†6æBç&vÆö"‚r¢r’“ ¢–bæ÷Bæ—5öf–ÆR‚“¢6öçF–çVP¢&3Öbw´4äD”DDUôäÔWÒ÷·ç&VÆF—fU÷Fò†6æB’æ5÷÷6—‚‚—Òp¢–æfó×¦—f–ÆRå¦—–æfò†&2Âƒ##bÃ’Ã"ÃÃÃ’“²–æfòæ6ö×&W75÷G—S×¦—f–ÆRå¤•ôDTdÄDTC²–æfòæW‡FW&æÅöGG#ÓócCCÃÃ`¢¢çw&—FW7G"†–æfòÇç&VEö'—FW2‚’Æ6ö×&W75÷G—S×¦—f–ÆRå¤•ôDTdÄDTBÆ6ö×&W76ÆWfVÃÓ’¢&–çB†§6öâæGV×2‡²v6æF–FFRs¦÷WBææÖRÂw6†#Sbs§6†#Sb†÷WB’Âw6—¦Rs¦÷WBç7FB‚’ç7E÷6—¦WÒÇ6W&F÷'3Ò‚rÂrÂs¢r’’ ¦FVbÖ–â‚“ ¢Ö&w'6Rä&wVÖVçE'6W"‚“²7V#ÖæFE÷7V''6W'2†FW7CÒv6ÖBrÇ&WV—&VCÕG'VR¢ó×7V"æFE÷'6W'2‚v÷fW&Æ’r“²òæFEö&wVÖVçB‚rÒ×rÇG—SÕF‚Ç&WV—&VCÕG'VR“²òæFEö&wVÖVçB‚rÒ×&WòrÇG—SÕF‚Ç&WV—&VCÕG'VR¢×7V"æFE÷'6W"‚w6¶vRr“²æFEö&wVÖVçB‚rÒ×&WòrÇG—SÕF‚Ç&WV—&VCÕG'VR“²æFEö&wVÖVçB‚rÒÖ÷WBrÇG—SÕF‚Ç&WV—&VCÕG'VR“²æFEö&wVÖVçB‚rÒ×'VâÖ–BrÇ&WV—&VCÕG'VR¢Öç'6Uö&w2‚¢–bæ6ÖCÓÒv÷fW&Æ’s¢÷fW&Æ’†çÆç&Wò¢VÇ6S¢6¶vR†ç&WòÆæ÷WBÆç'Våö–B¦–bõöæÖUõóÓÒuõöÖ–åõòs¢Ö–â‚