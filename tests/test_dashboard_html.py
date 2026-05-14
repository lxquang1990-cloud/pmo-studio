from pathlib import Path
from tempfile import TemporaryDirectory

from pmo_studio.core.project import Project, ProjectConfig
from pmo_studio.core.signoff import update_signoff
from pmo_studio.exporters.static_html import export_static


def test_dashboard_html_has_modern_sections_and_signoff():
    with TemporaryDirectory() as td:
        p = Project(Path(td) / "html", ProjectConfig(project_slug="html", customer="Demo"))
        p.ensure_layout(); p.save()
        update_signoff(p, "BA", "approved", approved_by="QA")
        out = export_static(p.root)
        text = out.read_text(encoding="utf-8")
        assert "PMO Studio" in text
        assert "Sign-off" in text
        assert "Domain Detection" in text
        assert "Export lock" in text
        assert "grid" in text
