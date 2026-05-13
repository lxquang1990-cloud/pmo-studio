"""Static view-only dashboard exporter."""
from __future__ import annotations

import json
from pathlib import Path


def _json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def export_static(project_root: Path) -> Path:
    out_dir = project_root / "exports" / "management"
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts = sorted([p.relative_to(project_root) for p in (project_root / "artifacts").rglob("*") if p.is_file()])
    quality = sorted([p.relative_to(project_root) for p in (project_root / "quality").rglob("*.json") if p.is_file()])
    baselines = sorted([p.relative_to(project_root) for p in (project_root / "baselines").rglob("manifest.json") if p.is_file()])
    crs = sorted([p.relative_to(project_root) for p in (project_root / "change-requests").glob("CR-*.md") if p.is_file()])
    state = _json(project_root / "state.json") or {}
    config = _json(project_root / "config.json") or {}

    def lis(items):
        return "\n".join(f"<li><code>{p}</code></li>" for p in items) or "<li>None</li>"

    gate_rows = []
    for rel in quality:
        data = _json(project_root / rel) or {}
        gate_rows.append(f"<tr><td><code>{rel}</code></td><td>{data.get('layer')}</td><td class='{('pass' if data.get('passed') else 'fail')}'>{data.get('passed')}</td></tr>")

    html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>PMO Studio Dashboard</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;max-width:1100px;margin:40px auto;line-height:1.5;color:#222}}
code{{background:#f2f2f2;padding:2px 4px;border-radius:4px}} .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.card{{border:1px solid #ddd;border-radius:10px;padding:14px;background:#fff}} .num{{font-size:28px;font-weight:700}} .pass{{color:#0a7f36;font-weight:700}} .fail{{color:#b00020;font-weight:700}}
table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #ddd;padding:6px}} th{{background:#fafafa}}
</style></head>
<body>
<h1>PMO Studio Dashboard</h1>
<p>Project: <strong>{config.get('project_slug','')}</strong> · Customer: <strong>{config.get('customer','')}</strong> · State: <strong>{state.get('lifecycle_state','')}</strong></p>
<div class='grid'>
<div class='card'><div>Artifacts</div><div class='num'>{len(artifacts)}</div></div>
<div class='card'><div>Gate Results</div><div class='num'>{len(quality)}</div></div>
<div class='card'><div>Baselines</div><div class='num'>{len(baselines)}</div></div>
<div class='card'><div>Change Requests</div><div class='num'>{len(crs)}</div></div>
</div>
<h2>Quality Gates</h2><table><tr><th>File</th><th>Layer</th><th>Passed</th></tr>{''.join(gate_rows) or '<tr><td colspan="3">None</td></tr>'}</table>
<h2>Baselines</h2><ul>{lis(baselines)}</ul>
<h2>Change Requests</h2><ul>{lis(crs)}</ul>
<h2>Artifacts</h2><ul>{lis(artifacts)}</ul>
</body></html>
"""
    path = out_dir / "index.html"
    path.write_text(html, encoding="utf-8")
    return path
