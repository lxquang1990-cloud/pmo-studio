"""Static view-only dashboard exporter."""
from __future__ import annotations

import html as html_lib
import json
from pathlib import Path

from pmo_studio.core.signoff import assert_export_allowed


def _json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def export_static(project_root: Path, force: bool = False) -> Path:
    assert_export_allowed(project_root, force=force)
    out_dir = project_root / "exports" / "management"
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts = sorted([p.relative_to(project_root) for p in (project_root / "artifacts").rglob("*") if p.is_file()])
    quality = sorted([p.relative_to(project_root) for p in (project_root / "quality").rglob("*.json") if p.is_file()])
    baselines = sorted([p.relative_to(project_root) for p in (project_root / "baselines").rglob("manifest.json") if p.is_file()])
    crs = sorted([p.relative_to(project_root) for p in (project_root / "change-requests").glob("CR-*.md") if p.is_file()])
    exports = sorted([p.relative_to(project_root) for p in (project_root / "exports").rglob("*") if p.is_file()])
    state = _json(project_root / "state.json") or {}
    config = _json(project_root / "config.json") or {}
    detection = _json(project_root / "artifacts" / "stage-0" / "domain-detection.json") or {}
    signoff = _json(project_root / "review" / "signoff.json") or {"locked": False, "approvals": {}}
    trace = _json(project_root / "traceability" / "views" / "validation.json") or {}
    quality_summary = _json(project_root / "quality" / "summary.json") or {}

    def esc(v):
        return html_lib.escape(str(v))

    def lis(items):
        return "\n".join(f"<li><code>{esc(p)}</code></li>" for p in items) or "<li>None</li>"

    gate_rows = []
    for rel in quality:
        data = _json(project_root / rel) or {}
        cls = "pass" if data.get("passed") else "fail"
        gate_rows.append(f"<tr><td><code>{esc(rel)}</code></td><td>{esc(data.get('layer',''))}</td><td class='{cls}'>{esc(data.get('passed'))}</td></tr>")

    approval_rows = []
    for role, entry in sorted((signoff.get("approvals") or {}).items()):
        cls = "pass" if entry.get("status") == "approved" else "warn" if entry.get("status") == "pending" else "fail"
        approval_rows.append(f"<tr><td>{esc(role)}</td><td class='{cls}'>{esc(entry.get('status'))}</td><td>{esc(entry.get('approved_by',''))}</td><td>{esc(entry.get('updated_at',''))}</td><td>{esc(entry.get('note',''))}</td></tr>")

    trace_status = "PASS" if trace.get("passed") else "WARN" if trace else "NOT RUN"
    trace_cls = "pass" if trace.get("passed") else "warn"
    locked_badge = "LOCKED" if signoff.get("locked") else "OPEN"
    locked_cls = "fail" if signoff.get("locked") else "pass"

    html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>PMO Studio Dashboard</title>
<style>
:root{{--bg:#f6f8fb;--card:#fff;--text:#172033;--muted:#667085;--line:#e5e7eb;--blue:#2557d6;--green:#087443;--red:#b42318;--amber:#b54708}}
*{{box-sizing:border-box}} body{{font-family:Inter,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:0;background:var(--bg);color:var(--text);line-height:1.5}}
.wrap{{max-width:1220px;margin:0 auto;padding:32px}} .hero{{background:linear-gradient(135deg,#1f3864,#2557d6);color:white;border-radius:22px;padding:28px;margin-bottom:20px;box-shadow:0 12px 40px rgba(31,56,100,.22)}}
.hero h1{{margin:0 0 8px;font-size:32px}} .hero p{{margin:0;color:#dbe7ff}} .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0}}
.card{{border:1px solid var(--line);border-radius:18px;padding:18px;background:var(--card);box-shadow:0 6px 22px rgba(16,24,40,.06)}} .label{{color:var(--muted);font-size:13px}} .num{{font-size:30px;font-weight:800;margin-top:4px}}
.badge{{display:inline-block;padding:4px 10px;border-radius:999px;background:#eef4ff;color:#2557d6;font-weight:700;font-size:12px}} .pass{{color:var(--green);font-weight:800}} .fail{{color:var(--red);font-weight:800}} .warn{{color:var(--amber);font-weight:800}}
code{{background:#f2f4f7;padding:2px 6px;border-radius:6px}} table{{border-collapse:collapse;width:100%;background:white;border-radius:12px;overflow:hidden}} td,th{{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}} th{{background:#f9fafb;color:#475467;font-size:13px}}
.section{{margin-top:18px}} details{{background:white;border:1px solid var(--line);border-radius:16px;padding:14px;margin-top:12px}} summary{{cursor:pointer;font-weight:800}} ul{{margin-top:8px}}
@media(max-width:900px){{.grid{{grid-template-columns:repeat(2,1fr)}}}} @media(max-width:560px){{.grid{{grid-template-columns:1fr}}.wrap{{padding:16px}}}}
</style></head>
<body><div class='wrap'>
<div class='hero'><span class='badge'>PMO Studio</span><h1>{esc(config.get('project_slug',''))}</h1><p>Customer: <strong>{esc(config.get('customer',''))}</strong> · State: <strong>{esc(state.get('lifecycle_state',''))}</strong> · Export lock: <strong class='{locked_cls}'>{locked_badge}</strong></p></div>
<div class='grid'>
<div class='card'><div class='label'>Artifacts</div><div class='num'>{len(artifacts)}</div></div>
<div class='card'><div class='label'>Quality</div><div class='num'>{esc(quality_summary.get('passed',0))}/{esc(quality_summary.get('total',0))}</div></div>
<div class='card'><div class='label'>Traceability</div><div class='num {trace_cls}'>{trace_status}</div></div>
<div class='card'><div class='label'>Domain</div><div class='num' style='font-size:20px'>{esc(detection.get('selected_domain','n/a'))}</div><div class='label'>{esc(detection.get('confidence',''))} · score {esc(detection.get('score',''))}</div></div>
</div>
<div class='card section'><h2>Domain Detection</h2><p>{esc(detection.get('explanation','Run pmo detect-domain to generate detection.'))}</p></div>
<div class='card section'><h2>Sign-off</h2><table><tr><th>Role</th><th>Status</th><th>By</th><th>Updated</th><th>Note</th></tr>{''.join(approval_rows) or '<tr><td colspan="5">No sign-off yet</td></tr>'}</table></div>
<div class='card section'><h2>Quality Gates</h2><table><tr><th>File</th><th>Layer</th><th>Passed</th></tr>{''.join(gate_rows) or '<tr><td colspan="3">None</td></tr>'}</table></div>
<details open><summary>Exports</summary><ul>{lis(exports)}</ul></details>
<details><summary>Baselines</summary><ul>{lis(baselines)}</ul></details>
<details><summary>Change Requests</summary><ul>{lis(crs)}</ul></details>
<details><summary>Artifacts</summary><ul>{lis(artifacts)}</ul></details>
</div></body></html>
"""
    path = out_dir / "index.html"
    path.write_text(html, encoding="utf-8")
    return path
