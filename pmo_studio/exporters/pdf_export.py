"""PDF exports for PMO Studio."""
from __future__ import annotations

import json
from datetime import datetime
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


def export_pdf(project_root: Path, profile: str = "client-ready", force: bool = False) -> Path:
    """Generate a real PDF using reportlab.

    This intentionally keeps PDF output dependency-light and deterministic. The
    professional DOCX remains the rich artifact; PDF is an executive/governance
    companion with project metadata, quality, traceability, sign-off and artifact index.
    """
    assert_export_allowed(project_root, force=force)
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PDF backend unavailable. Install reportlab or use --format pdf-html.") from exc

    out_dir = project_root / "exports" / profile
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "pmo-documentation-pack.pdf"
    config = _json(project_root / "config.json") or {}
    state = _json(project_root / "state.json") or {}
    manifest = _json(project_root / "artifacts/manifest.json") or {}
    quality = _json(project_root / "quality/summary.json") or {}
    trace = _json(project_root / "traceability/views/validation.json") or {}
    signoff = _json(project_root / "review/signoff.json") or {}
    artifacts = sorted(p.relative_to(project_root).as_posix() for p in (project_root / "artifacts").rglob("*") if p.is_file()) if (project_root / "artifacts").exists() else []

    doc = SimpleDocTemplate(str(out), pagesize=A4, title="PMO Studio Documentation Pack")
    styles = getSampleStyleSheet()
    story = [Paragraph("PMO Studio Documentation Pack", styles["Title"]), Spacer(1, 12)]
    rows = [
        ["Project", config.get("project_slug", project_root.name)],
        ["Customer", config.get("customer", "N/A")],
        ["Lifecycle", state.get("lifecycle_state", "N/A")],
        ["Generated", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["Generator", manifest.get("generator_version", "N/A")],
        ["Domain", manifest.get("domain_pack", "N/A")],
        ["Quality", f"{quality.get('passed', 0)}/{quality.get('total', 0)} passed"],
        ["Traceability", "PASS" if trace.get("passed") else "WARN"],
        ["Sign-off locked", str(signoff.get("locked", False))],
    ]
    story.append(_table(rows, Table, TableStyle, colors))
    story += [Spacer(1, 14), Paragraph("Artifact Manifest", styles["Heading1"])]
    story.append(Paragraph(f"Source hash: {manifest.get('source_hash', '')[:32]}", styles["BodyText"]))
    story.append(Paragraph(f"Template hash: {manifest.get('template_tree_hash', '')[:32]}", styles["BodyText"]))
    story += [Spacer(1, 14), Paragraph("Artifact Index", styles["Heading1"])]
    for rel in artifacts[:80]:
        story.append(Paragraph(f"• {rel}", styles["BodyText"]))
    doc.build(story)
    return out


def _table(rows, Table, TableStyle, colors):
    t = Table(rows, colWidths=[120, 360])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF4FF")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    return t


def _json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
