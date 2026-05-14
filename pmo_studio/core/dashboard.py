"""Per-project dashboard/index and review checklist generation."""
from __future__ import annotations

import json
from pathlib import Path

from pmo_studio.core.lifecycle import summarize_project


def generate_project_index(project) -> tuple[Path, Path]:
    project.root.mkdir(parents=True, exist_ok=True)
    summary = summarize_project(project)
    detection = _load_json(project.root / "artifacts/stage-0/domain-detection.json")
    quality = _quality_text(summary)
    trace = _trace_text(summary)
    artifacts = sorted(p.relative_to(project.root) for p in (project.root / "artifacts").rglob("*") if p.is_file())
    exports = sorted(p.relative_to(project.root) for p in (project.root / "exports").rglob("*") if p.is_file())
    md = project.root / "PROJECT_INDEX.md"
    html = project.root / "index.html"
    md.write_text(_markdown(project, summary, detection, quality, trace, artifacts, exports), encoding="utf-8")
    html.write_text(_html(md.read_text(encoding="utf-8")), encoding="utf-8")
    return md, html


def generate_review_checklist(project) -> Path:
    out = project.root / "review" / "checklist.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"""# Review Checklist: {project.config.project_slug}

## PO
- [ ] Vision đúng business objective và source đầu vào.
- [ ] Roadmap/release plan hợp lý.
- [ ] Backlog có priority và acceptance linkage.

## PM
- [ ] Charter/scope rõ ràng.
- [ ] WBS/RACI đủ role và responsibility.
- [ ] Risk register có mitigation và owner.

## BA
- [ ] PRD/BRD/SRS đúng source, không leak domain khác.
- [ ] User Stories/AC testable.
- [ ] Test cases cover AC.
- [ ] Quotation đúng scope và có rationale.

## IC
- [ ] Fit-gap đúng module.
- [ ] Config workbook đủ field/workflow.
- [ ] UAT/deployment/cutover khả thi.

## Final Sign-off
- [ ] Quality Gates PASS.
- [ ] Traceability PASS hoặc exception được approve.
- [ ] Quotation reviewed by human.
- [ ] Customer export package reviewed.
""", encoding="utf-8")
    return out


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _quality_text(summary) -> str:
    if not getattr(summary, "gate_total", 0):
        return "Not run"
    return f"{summary.gate_passed}/{summary.gate_total} passed, failed={summary.gate_failed}"


def _trace_text(summary) -> str:
    if getattr(summary, "trace_passed", None) is None:
        return "Not run"
    status = "PASS" if summary.trace_passed else "WARN"
    return f"{status} ({summary.trace_nodes or 0} nodes/{summary.trace_edges or 0} edges)"


def _markdown(project, summary, detection: dict, quality: str, trace: str, artifacts: list[Path], exports: list[Path]) -> str:
    artifact_lines = "\n".join(f"- `{p}`" for p in artifacts[:80]) or "- No artifacts yet"
    export_lines = "\n".join(f"- `{p}`" for p in exports[:30]) or "- No exports yet"
    return f"""# PMO Project: {project.config.project_slug}

## Status
- Customer: {project.config.customer}
- Lifecycle: {summary.state}
- Current stage: {summary.current_stage or 'N/A'}
- Domain: {detection.get('selected_domain', 'not detected')} ({detection.get('confidence', 'n/a')}, score={detection.get('score', 'n/a')})
- Quality: {quality}
- Traceability: {trace}
- Root: `{project.root}`

## Domain Detection
{detection.get('explanation', 'Run `pmo detect-domain <slug>` to generate domain detection.')}

## Inputs
- `source/uploads/` — original user files; never included in customer ZIP by default.
- `source/redacted/` — sanitized source used by generators.

## Artifacts
{artifact_lines}

## Exports
{export_lines}

## Review
- Checklist: `review/checklist.md`
- Sign-off policy: human approval required for official quotation/baseline.

## Useful Commands
```bash
pmo detect-domain {project.config.project_slug}
pmo generate {project.config.project_slug} all --from-sources --llm noop --no-refine
pmo trace {project.config.project_slug} --validate
pmo run-gates {project.config.project_slug} --include-c --llm noop
pmo export {project.config.project_slug} --format all --profile customer
pmo index {project.config.project_slug}
```
"""


def _html(markdown: str) -> str:
    import html
    body = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.startswith("```"):
            continue
        else:
            body.append(f"<p>{html.escape(line)}</p>" if line else "")
    return "<!doctype html><html><head><meta charset='utf-8'><title>PMO Project Index</title></head><body>" + "\n".join(body) + "</body></html>\n"
