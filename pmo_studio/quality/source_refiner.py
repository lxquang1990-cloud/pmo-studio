"""Source-grounded Refiner (v2.7)."""
from __future__ import annotations
import json, re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from pmo_studio.generators.source_ba import read_redacted_sources
from pmo_studio.quality.intelligence import _important_terms, _project_stub


def _source_terms(source: str, max_terms: int) -> list[str]:
    terms = _important_terms(source)
    for acronym in re.findall(r"\b[A-Z0-9]{3,}\b", source):
        if acronym not in terms:
            terms.insert(0, acronym)
    out = []
    for term in terms:
        if term.lower() not in [x.lower() for x in out]:
            out.append(term)
    return out[:max_terms]

@dataclass
class SourceRefinement:
    term: str; action: str; target: str
@dataclass
class SourceRefinerReport:
    schema: str; created_at: str; project_slug: str; source_terms: list[str]; refinements: list[SourceRefinement]

def refine_from_sources(project_root: Path, apply: bool=True, max_terms:int=12) -> SourceRefinerReport:
    source=read_redacted_sources(_project_stub(project_root)); terms=_source_terms(source, max_terms)
    artifacts={p: p.read_text(encoding='utf-8', errors='replace') for p in project_root.glob('artifacts/ba/**/*.md') if p.is_file()}
    combined='\n'.join(artifacts.values()).lower(); refs=[]
    missing=[t for t in terms if t.lower() not in combined]
    if missing:
        target=project_root/'artifacts'/'ba'/'02-brd.md'
        addition='\n\n## Source-grounded Coverage Notes\n' + '\n'.join(f"- Source term retained for review: **{t}**." for t in missing) + '\n'
        if apply and target.exists() and '## Source-grounded Coverage Notes' not in target.read_text(encoding='utf-8', errors='replace'):
            target.write_text(target.read_text(encoding='utf-8')+addition, encoding='utf-8')
        refs=[SourceRefinement(t,'added_coverage_note','artifacts/ba/02-brd.md') for t in missing]
    return SourceRefinerReport('pmo.source_refiner.v1', datetime.now(timezone.utc).isoformat(), project_root.name, terms, refs)

def write_source_refinement(project_root: Path, apply: bool=True) -> Path:
    r=refine_from_sources(project_root, apply=apply)
    out=project_root/'quality'/'source-refiner.json'; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(r), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    md=[f"# Source-grounded Refiner: {r.project_slug}","",f"- Source terms checked: {len(r.source_terms)}",f"- Refinements: {len(r.refinements)}",""]
    md += [f"- {x.term}: {x.action} → {x.target}" for x in r.refinements] or ['No refinement needed.']
    (project_root/'quality'/'source-refiner.md').write_text('\n'.join(md)+'\n', encoding='utf-8')
    return out
