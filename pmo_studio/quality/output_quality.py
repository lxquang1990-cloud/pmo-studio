"""Output Quality Upgrade (v2.6).

Deterministic customer-facing artifact polishing and scoring. The module is
conservative: it never invents new scope, it normalizes common weak wording and
writes an audit trail of changed files.
"""
from __future__ import annotations

import json, re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

TARGETS = ["artifacts/ba/01-prd.md","artifacts/ba/02-brd.md","artifacts/ba/03-srs/srs.md","artifacts/ba/05-test-cases.md","artifacts/ic/04-uat-plan.md"]
WEAK = {"TBD":"Assumption: pending customer confirmation","TODO":"Assumption: pending customer confirmation","FIXME":"Assumption: pending customer confirmation","lorem ipsum":"Assumption: source content pending confirmation","chưa xác định":"Giả định: cần khách hàng xác nhận trong workshop kế tiếp","cần bổ sung":"Giả định: cần bổ sung sau khi khách hàng xác nhận"}

@dataclass
class OutputQualityChange:
    path: str; replacements: int; headings_added: list[str] = field(default_factory=list)

@dataclass
class OutputQualityReport:
    schema: str; created_at: str; project_slug: str; score: int; changed_files: list[OutputQualityChange]; findings: list[str]

def upgrade_output_quality(project_root: Path, apply: bool = True) -> OutputQualityReport:
    changes=[]; findings=[]
    for rel in TARGETS:
        p=project_root/rel
        if not p.exists():
            findings.append(f"missing:{rel}"); continue
        text=p.read_text(encoding='utf-8', errors='replace')
        new=text; repl=0; headings=[]
        for a,b in WEAK.items():
            new,n=re.subn(re.escape(a), b, new, flags=re.I); repl+=n
        if rel.endswith(('01-prd.md','02-brd.md','srs.md')) and not re.search(r'^## .*?(Assumption|Giả định|Scope Boundary|Phạm vi)', new, flags=re.I|re.M):
            new += "\n\n## Scope Boundaries / Giả định\n- Nội dung được baseline theo source hiện có; các điểm chưa có dữ liệu được quản lý như assumption và cần xác nhận trong workshop.\n"
            headings.append('Scope Boundaries / Giả định')
        if rel.endswith(('05-test-cases.md','04-uat-plan.md')) and not re.search(r'Expected Result|Kết quả mong đợi|Pass/Fail', new, flags=re.I):
            new += "\n\n## Execution Guidance\n- Mỗi test case cần có Expected Result/Kết quả mong đợi, dữ liệu test, trạng thái Pass/Fail và evidence khi UAT.\n"
            headings.append('Execution Guidance')
        if new!=text:
            changes.append(OutputQualityChange(rel,repl,headings))
            if apply: p.write_text(new, encoding='utf-8')
    penalty=len(findings)*12 + sum(c.replacements for c in changes)*2
    return OutputQualityReport('pmo.output_quality.v1', datetime.now(timezone.utc).isoformat(), project_root.name, max(0,100-penalty), changes, findings)

def write_output_quality(project_root: Path, apply: bool=True) -> Path:
    r=upgrade_output_quality(project_root, apply=apply)
    out=project_root/'quality'/'output-quality.json'; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(r), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    md=[f"# Output Quality Upgrade: {r.project_slug}","",f"- Score: {r.score}/100",f"- Changed files: {len(r.changed_files)}",f"- Findings: {len(r.findings)}",""]
    for c in r.changed_files: md.append(f"- {c.path}: replacements={c.replacements}, headings_added={', '.join(c.headings_added) or '-'}")
    if r.findings: md += ["","## Findings", *[f"- {x}" for x in r.findings]]
    (project_root/'quality'/'output-quality.md').write_text('\n'.join(md)+'\n', encoding='utf-8')
    return out
