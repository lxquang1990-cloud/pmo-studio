from __future__ import annotations
import json,re
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from pathlib import Path
from pmo_studio.model.builder import load_ba_model

PLACEHOLDER=re.compile(r'(\$\{[^}]+\}|\{\{[^}]+\}\}|\bTBD\b|\bTODO\b|\bFIXME\b|lorem ipsum|chưa xác định|cần bổ sung)',re.I)
GENERIC=[r'System shall support .* where applicable',r'source-defined modules',r'Execute business workflow',r'Validate scenario \d+',r'Data is validated, saved/processed',r'Feature score 100/100',r'Trace: FEAT-']
@dataclass
class Finding: id:str; severity:str; message:str; artifact:str=''; evidence:str=''
@dataclass
class QualityV3Report: schema:str; created_at:str; project_slug:str; score:int; readiness:str; findings:list[Finding]

def run_quality_v3(project_root:Path, scope:str='all')->QualityV3Report:
    findings=[]
    if scope == 'customer':
        files=list((project_root/'exports/customer').rglob('*.md')) + list((project_root/'artifacts/ba/03-srs').glob('srs-customer-ready.*.md')) + list((project_root/'artifacts/ba/04-us').glob('user-stories.*.md'))
    else:
        files=list((project_root/'artifacts').rglob('*.md'))+list((project_root/'exports/customer').rglob('*.md'))
    for p in files:
        txt=p.read_text(encoding='utf-8',errors='replace')
        if m:=PLACEHOLDER.search(txt): findings.append(Finding('Q3-PLACEHOLDER','high','Placeholder/template token remains',str(p.relative_to(project_root)),m.group(0)))
        for i,pat in enumerate(GENERIC,1):
            if re.search(pat,txt,re.I): findings.append(Finding(f'Q3-GENERIC-{i:02d}','medium','Generic/non-customer-ready phrase found',str(p.relative_to(project_root)),pat))
    mp=project_root/'artifacts/model/ba-model.json'
    if not mp.exists(): findings.append(Finding('Q3-MODEL-MISSING','high','Canonical BA model is missing','artifacts/model/ba-model.json'))
    else:
        m=load_ba_model(project_root)
        if len(m.features)>len(m.requirements): findings.append(Finding('Q3-COVERAGE-REQ','high','Some features have no requirements'))
        reqs={r.id for r in m.requirements}; ac_req={a.requirement_id for a in m.acceptance_criteria}; tc_ac={t.acceptance_criteria_id for t in m.test_cases}; acs={a.id for a in m.acceptance_criteria}
        if reqs-ac_req: findings.append(Finding('Q3-COVERAGE-AC','high','Some requirements have no AC',evidence=', '.join(sorted(reqs-ac_req)[:10])))
        if acs-tc_ac: findings.append(Finding('Q3-COVERAGE-TC','high','Some AC have no test case',evidence=', '.join(sorted(acs-tc_ac)[:10])))
    score=max(0,100-sum({'high':25,'medium':10,'low':5}.get(f.severity,5) for f in findings)); readiness='READY' if score>=90 and not any(f.severity=='high' for f in findings) else 'NEEDS_REVIEW' if score>=70 else 'NOT_READY'
    return QualityV3Report('pmo.quality_v3.v1',datetime.now(timezone.utc).isoformat(),project_root.name,score,readiness,findings)

def write_quality_v3(project_root:Path, scope:str='all')->Path:
    r=run_quality_v3(project_root, scope=scope); out=project_root/(f'quality/customer-review-v3.{scope}.json' if scope != 'all' else 'quality/customer-review-v3.json'); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(asdict(r),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    md=[f'# Customer Review v3: {r.project_slug}','',f'- Readiness: **{r.readiness}**',f'- Score: **{r.score}/100**',f'- Findings: **{len(r.findings)}**','']
    md += ['No issues found.'] if not r.findings else ['| ID | Severity | Artifact | Message | Evidence |','|---|---|---|---|---|',*[f'| {f.id} | {f.severity} | {f.artifact} | {f.message} | {f.evidence} |' for f in r.findings]]
    (project_root/(f'quality/customer-review-v3.{scope}.md' if scope != 'all' else 'quality/customer-review-v3.md')).write_text('\n'.join(md)+'\n',encoding='utf-8')
    return out
