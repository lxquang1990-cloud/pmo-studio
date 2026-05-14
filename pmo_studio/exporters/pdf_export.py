"""PDF-ready HTML export.

PMO Studio avoids adding heavyweight PDF rendering dependencies by default. This
export creates a print-optimized HTML file that browsers or CI can convert to PDF.
"""
from __future__ import annotations

from pathlib import Path

from pmo_studio.core.signoff import assert_export_allowed
from pmo_studio.exporters.static_html import export_static


def export_pdf_ready_html(project_root: Path, profile: str = "client-ready", force: bool = False) -> Path:
    assert_export_allowed(project_root, force=force)
    dashboard = export_static(project_root, force=True)
    html = dashboard.read_text(encoding="utf-8")
    print_css = """
<style>
@media print {
  body { background: white !important; }
  .wrap { max-width: none; padding: 12mm; }
  .card, details, .hero { box-shadow: none !important; break-inside: avoid; }
  details { page-break-inside: avoid; }
  .hero { background: #1f3864 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
</style>
"""
    html = html.replace("</head>", print_css + "</head>")
    out_dir = project_root / "exports" / profile
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "pmo-dashboard-print-ready.html"
    out.write_text(html, encoding="utf-8")
    return out
