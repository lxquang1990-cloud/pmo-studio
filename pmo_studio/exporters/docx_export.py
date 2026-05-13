"""DOCX exporter for client/internal profiles."""
from __future__ import annotations

from pathlib import Path

try:
    from docx import Document
except Exception:  # pragma: no cover
    Document = None


def _is_md_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _parse_table(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and all(set(c) <= {"-", ":", " "} for c in cells):
            continue
        rows.append(cells)
    return rows


def _add_table(document, table_lines: list[str]) -> None:
    rows = _parse_table(table_lines)
    if not rows:
        return
    width = max(len(r) for r in rows)
    table = document.add_table(rows=len(rows), cols=width)
    table.style = "Table Grid"
    for r_idx, row in enumerate(rows):
        for c_idx in range(width):
            table.cell(r_idx, c_idx).text = row[c_idx] if c_idx < len(row) else ""


def _flush_table(document, table_buffer: list[str]) -> None:
    if table_buffer:
        _add_table(document, table_buffer)
        table_buffer.clear()


def _add_markdown(document, text: str) -> None:
    table_buffer: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if _is_md_table_line(stripped):
            table_buffer.append(stripped)
            continue
        _flush_table(document, table_buffer)
        if stripped.startswith("# "):
            document.add_heading(stripped[2:], level=1)
        elif stripped.startswith("## "):
            document.add_heading(stripped[3:], level=2)
        elif stripped.startswith("### "):
            document.add_heading(stripped[4:], level=3)
        elif stripped.startswith("- "):
            document.add_paragraph(stripped[2:], style="List Bullet")
        elif stripped:
            document.add_paragraph(stripped)
    _flush_table(document, table_buffer)


def export_docx(project_root: Path, profile: str = "client-ready") -> Path:
    if Document is None:
        raise RuntimeError("python-docx is not installed")
    doc = Document()
    doc.add_heading("PMO Studio Documentation Pack", 0)
    doc.add_paragraph(f"Profile: {profile}")
    order = [
        "artifacts/stage-0/project-brief.md",
        "artifacts/po/01-vision.md",
        "artifacts/pm/01-charter.md",
        "artifacts/ba/01-prd.md",
        "artifacts/ba/02-brd.md",
        "artifacts/ba/03-srs/srs.md",
        "artifacts/ba/05-test-cases.md",
        "artifacts/ic/03-deployment-plan.md",
        "artifacts/ic/04-uat-plan.md",
        "traceability/rtm.md",
    ]
    for rel in order:
        path = project_root / rel
        if path.exists():
            doc.add_page_break()
            _add_markdown(doc, path.read_text(encoding="utf-8", errors="ignore"))
    out_dir = project_root / "exports" / profile
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "pmo-documentation-pack.docx"
    doc.save(out)
    return out
