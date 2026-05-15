from __future__ import annotations
from pathlib import Path
import tempfile, yaml
from dataclasses import dataclass
from pmo_studio.core.project import Project
from pmo_studio.generators.stage0 import generate_stage0
from pmo_studio.model.builder import write_ba_model, load_ba_model

@dataclass
class GoldenResult:
    name: str; passed: bool; findings: list[str]

def run_golden_eval(root: Path | None = None) -> list[GoldenResult]:
    base=root or Path('examples/golden')
    results=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for case in sorted([p for p in base.iterdir() if p.is_dir()]):
            exp=yaml.safe_load((case/'expected-keypoints.yaml').read_text(encoding='utf-8'))
            text=(case/'source.md').read_text(encoding='utf-8')
            p=Project.create(f'golden-{case.name.replace('_','-')}', customer='Golden', root_base=tmp)
            generate_stage0(p, brief=text[:120], products=['Golden'], sources=[case/'source.md'])
            write_ba_model(p); m=load_ba_model(p.root)
            names='\n'.join(f.name for f in m.features)
            findings=[]
            if m.domain.id != exp['domain']: findings.append(f'domain expected {exp["domain"]}, got {m.domain.id}')
            for f in exp.get('must_have_features',[]):
                if f not in names: findings.append(f'missing feature: {f}')
            for f in exp.get('blocked_features',[]):
                if f in names: findings.append(f'blocked feature present: {f}')
            results.append(GoldenResult(case.name, not findings, findings))
    return results
