from pathlib import Path
from tempfile import TemporaryDirectory

from pmo_studio.core.project import Project, ProjectConfig
from pmo_studio.generators.po_pm_ic import generate_po, generate_pm, generate_ic
from pmo_studio.generators.source_ba import generate_ba_from_sources
from pmo_studio.traceability.engine import TraceabilityEngine
from pmo_studio.traceability.validator import validate_traceability


def _run_project(slug: str, source: str):
    td = TemporaryDirectory()
    root = Path(td.name)
    project = Project(root / slug, ProjectConfig(project_slug=slug, customer="Demo"))
    project.ensure_layout(); project.save()
    (project.root / "source/redacted/source.md").write_text(source, encoding="utf-8")
    generate_po(project); generate_pm(project); generate_ba_from_sources(project); generate_ic(project)
    TraceabilityEngine(project.root).write_outputs()
    return td, project, validate_traceability(project.root)


def test_generic_crm_traceability_passes_without_domain_leakage():
    td, project, result = _run_project("crm-trace", """
| STT | CHỨC NĂNG | MÔ TẢ |
| 1 | Quản lý Lead | Capture and qualify leads |
| 2 | Quản lý Opportunity | Sales pipeline, forecast and approval workflow |
| 3 | Quản lý Customer | Customer profile, account history and reporting |
""")
    try:
        text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in (project.root / "artifacts").rglob("*.md")).lower()
        assert result.passed, result.missing_upstream
        assert "quản lý lead" in text
        assert "opportunity" in text
        assert "quản lý trang thiết bị" not in text
        assert "legaliq" not in text
    finally:
        td.cleanup()


def test_legal_traceability_passes():
    td, _project, result = _run_project("legal-trace", "LIQ LegalIQ hỏi đáp pháp lý, quản lý ủy quyền, hợp đồng, B.PCTT escalation.")
    try:
        assert result.passed, result.missing_upstream
    finally:
        td.cleanup()
