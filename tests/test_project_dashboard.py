from pathlib import Path
from tempfile import TemporaryDirectory

from pmo_studio.core.project import Project, ProjectConfig
from pmo_studio.core.dashboard import generate_project_index, generate_review_checklist
from pmo_studio.domain.detector import detect_domain, write_domain_detection


def test_project_index_and_review_checklist_are_generated():
    with TemporaryDirectory() as td:
        p = Project(Path(td) / "dash", ProjectConfig(project_slug="dash", customer="Demo"))
        p.ensure_layout(); p.save()
        (p.root / "source/redacted/source.md").write_text("CRM quản lý Lead Opportunity", encoding="utf-8")
        write_domain_detection(p.root, detect_domain("CRM quản lý Lead Opportunity"))
        checklist = generate_review_checklist(p)
        md, html = generate_project_index(p)
        assert checklist.exists()
        assert md.exists()
        assert html.exists()
        text = md.read_text(encoding="utf-8")
        assert "PMO Project: dash" in text
        assert "Domain:" in text
        assert "review/checklist.md" in text
