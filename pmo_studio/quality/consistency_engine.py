"""Consistency Engine v2 (v2.9)."""
from __future__ import annotations
import json, re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

@dataclass
class ConsistencyFinding:
    id: str; severity: str; message: str; evidence: str=''
@dataclass
class ConsistencyReport:
    schema: str; created_at: str; project_slug: str; score: int; findings: list[ConsistencyFinding]

def _ids_by_prefix(text,prefix): return set(re.findall(rf'\b({prefix}-[A-Z0-9-]*\d+)\b', text))

def run_consistency_engine(project_root: Path) -> ConsistencyReport:
    files={str(p.relative_to(project_root)):p.read_text(encoding='utf-8',errors='replace') for p in project_root.glob('artifacts/**/*.md') if p.is_file()}
    text='\n'.join(files.values()); findings=[]
    for prefix in ['REQ','US','AC','TC']:
        ids=re.findall(rf'\b({prefix}-[A-Z0-9-]*\d+)\b', text); defs=re.findall(rf'^\s*(?:[#|`*\- ]*)({prefix}-[A-Z0-9-]*\d+)\b', text, flags=re.M)
        dup=sorted({x for x in defs if defs.count(x)>1})
        if dup: findings.append(ConsistencyFinding(f'CE-{prefix}-DUP','medium',f'Duplicate {prefix} definitions detected', ', '.join(dup[:10])))
    reqs=_ids_by_prefix(text,'REQ'); acs=_ids_by_prefix(text,'AC'); tcs=_ids_by_prefix(text,'TC')
    if reqs and not acs: findings.append(ConsistencyFinding('CE-TRACE-AC','high','Requirements exist but no Acceptance Criteria IDs found'))
    if acs and not tcs: findings.append(ConsistencyFinding('CE-TRACE-TC','high','Acceptance Criteria exist but no Test Case IDs found'))
    for rel,body in files.items():
        if '{{' in body or '}}' in body: findings.append(ConsistencyFinding('CE-TEMPLATE','high','Unrendered template token found',rel))
        if re.search(r'\b(TBD|TODO|FIXME|lorem ipsum)\b', body, re.I): findings.append(ConsistencyFinding('CE-PLACEHOLDER','medium','Placeholder remains',rel))
    score=max(0,100-sum({'high':25,'medium':12,'low':5}.get(f.severity,5) for f in findings))
    return ConsistencyReport('pmo.consistency_engine.v2', datetime.now(timezone.utc).isoformat(), project_root.name, score, findings)

def write_consistency_report(project_root: Path) -> Path:
    r=run_consistency_engine(project_root); out=project_root/'quality'/'consistency-engine.json'; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(asdict(r), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    md=[f"# Consistency Engine v2: {r.project_slug}","",f"- Score: {r.score}/100",f"- Findings: {len(r.findings)}",""]
    md += [f"- **{f.severity}** {f.id}: {f.message} {f.evidence}" for f in r.findings] or ['No consistency issues found.']
    (project_root/'quality'/'consistency-engine.md').write_text('\n'.join(md)+'\n', encoding='utf-8')
    return out
